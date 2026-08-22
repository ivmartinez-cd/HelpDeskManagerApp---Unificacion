"""Tests de integración de SqlAlchemyAuditStatisticsRepository (Postgres de test).

Cada método agrega en SQL sobre order_audit; acá se siembra la tabla a mano (created_at
elegido) y se verifica el agregado, el filtro por cliente/rango y la exclusión de dry-run.
"""

from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CANCELLED,
    EVENT_CREATED,
    EVENT_FAILED,
    ORDER_TYPE_INCIDENT,
)
from src.modules.insumos.domain.value_objects.audit_statistics import (
    DailyEventCount,
    SourceSplit,
)
from src.modules.insumos.infrastructure.models.order_audit_model import OrderAuditModel
from src.modules.insumos.infrastructure.repositories.sqlalchemy_audit_statistics_repository import (
    SqlAlchemyAuditStatisticsRepository,
)

_START = date(2026, 8, 1)
_END = date(2026, 8, 31)


def _at(day: int, hour: int = 15) -> datetime:
    """15:00 UTC = 12:00 en Argentina — lejos del corte de día."""
    return datetime(2026, 8, day, hour, 0, tzinfo=UTC)


async def _insert(db_session: AsyncSession, created_at: datetime, **overrides: object) -> None:
    values: dict[str, object] = {
        "event": EVENT_CREATED,
        "hp_request_id": 974325,
        "customer_id": 8,
        "customer_name": "Cliente Test",
        "sku": "CF230A",
        "description": "Toner negro",
        "device_serial": "SERIE1",
        "created_at": created_at,
    }
    values.update(overrides)
    db_session.add(OrderAuditModel(**values))
    await db_session.flush()


async def _seed(db_session: AsyncSession) -> None:
    await _insert(db_session, _at(10))
    await _insert(db_session, _at(10), sku="CF230X", description="Toner alto", device_serial="S2")
    await _insert(db_session, _at(11), detail="Pre-Correctivo — Auto-carga")
    await _insert(db_session, _at(12), event=EVENT_FAILED, detail="Sin stock")
    await _insert(db_session, _at(13), event=EVENT_FAILED, detail="")
    await _insert(db_session, _at(14), customer_id=9, customer_name="Otro Cliente")
    # No cuentan: dry-run, evento no auditado, fuera de rango.
    await _insert(db_session, _at(15), dry_run=True)
    await _insert(db_session, _at(15), event=EVENT_CANCELLED)
    await _insert(db_session, datetime(2026, 7, 31, 15, 0, tzinfo=UTC))


async def test_earliest_day_ignora_dry_run(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAuditStatisticsRepository(db_session)
    assert await repo.earliest_day() is None

    await _insert(db_session, _at(5), dry_run=True)
    await _insert(db_session, _at(9))

    assert await repo.earliest_day() == date(2026, 8, 9)


async def test_customer_name_toma_el_ultimo_no_vacio(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAuditStatisticsRepository(db_session)
    await _insert(db_session, _at(1), customer_name="Nombre Viejo")
    await _insert(db_session, _at(2), customer_name="Nombre Nuevo")
    await _insert(db_session, _at(3), customer_name="")
    await _insert(db_session, _at(4), customer_name=None)

    assert await repo.customer_name(8) == "Nombre Nuevo"
    assert await repo.customer_name(404) is None


async def test_daily_counts_y_event_totals(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAuditStatisticsRepository(db_session)
    await _seed(db_session)

    daily = await repo.daily_counts(_START, _END)
    assert [(d.day, d.event, d.count) for d in daily] == [
        (date(2026, 8, 10), EVENT_CREATED, 2),
        (date(2026, 8, 11), EVENT_CREATED, 1),
        (date(2026, 8, 12), EVENT_FAILED, 1),
        (date(2026, 8, 13), EVENT_FAILED, 1),
        (date(2026, 8, 14), EVENT_CREATED, 1),
    ]
    assert await repo.event_totals(_START, _END) == {EVENT_CREATED: 4, EVENT_FAILED: 2}
    assert await repo.event_totals(_START, _END, customer_id=9) == {EVENT_CREATED: 1}
    assert await repo.daily_counts(_START, _END, customer_id=9) == [
        DailyEventCount(day=date(2026, 8, 14), event=EVENT_CREATED, count=1)
    ]


async def test_customer_activity_rankea_por_total(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAuditStatisticsRepository(db_session)
    await _seed(db_session)
    await _insert(db_session, _at(16), customer_id=None, customer_name=None)

    activity = await repo.customer_activity(_START, _END)

    assert [(a.customer_id, a.customer_name, a.created, a.failed, a.total) for a in activity] == [
        (8, "Cliente Test", 3, 2, 5),
        (9, "Otro Cliente", 1, 0, 1),
    ]


async def test_top_skus_y_top_devices(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAuditStatisticsRepository(db_session)
    await _seed(db_session)
    await _insert(db_session, _at(17), sku=None, device_serial="")

    skus = await repo.top_skus(_START, _END, customer_id=8)
    assert [(s.sku, s.description, s.count) for s in skus] == [
        ("CF230A", "Toner negro", 2),
        ("CF230X", "Toner alto", 1),
    ]
    devices = await repo.top_devices(_START, _END, customer_id=8, limit=1)
    assert [(d.device_serial, d.count) for d in devices] == [("SERIE1", 2)]


async def test_failure_reasons_y_recent_failures(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAuditStatisticsRepository(db_session)
    await _seed(db_session)
    await _insert(db_session, _at(18), event=EVENT_FAILED, detail="Sin stock", sku="CF230X")

    reasons = await repo.failure_reasons(_START, _END, customer_id=8, limit=5)
    assert [(r.reason, r.count, r.last_at) for r in reasons] == [
        ("Sin stock", 2, _at(18)),
        ("Sin detalle", 1, _at(13)),
    ]
    recent = await repo.recent_failures(_START, _END, customer_id=8, limit=2)
    assert [(f.created_at, f.sku, f.device_serial, f.detail) for f in recent] == [
        (_at(18), "CF230X", "SERIE1", "Sin stock"),
        (_at(13), "CF230A", "SERIE1", ""),
    ]


async def test_source_split_cuenta_auto_carga_por_subcadena(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAuditStatisticsRepository(db_session)
    assert await repo.source_split(_START, _END, customer_id=8) == SourceSplit(auto=0, total=0)

    await _seed(db_session)

    split = await repo.source_split(_START, _END, customer_id=8)
    assert (split.auto, split.total) == (1, 3)


async def test_fulfillment_rows_solo_con_hp_request_time(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAuditStatisticsRepository(db_session)
    await _seed(db_session)
    await _insert(db_session, _at(20), hp_request_time=_at(19))

    rows = await repo.fulfillment_rows(_START, _END, customer_id=8)

    assert [(r.sku, r.device_serial, r.hp_request_time, r.created_at) for r in rows] == [
        ("CF230A", "SERIE1", _at(19), _at(20))
    ]


async def test_dispatch_rows_excluye_incidentes_y_dryrun(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAuditStatisticsRepository(db_session)
    await _seed(db_session)
    await _insert(db_session, _at(21), internal_order_id="441770-3")
    await _insert(db_session, _at(22), internal_order_id="DRYRUN-SDS-1")
    await _insert(
        db_session, _at(23), internal_order_id="500123-4", order_type=ORDER_TYPE_INCIDENT
    )

    rows = await repo.dispatch_rows(_START, _END, customer_id=8)

    assert [(r.sku, r.device_serial, r.internal_order_id, r.created_at) for r in rows] == [
        ("CF230A", "SERIE1", "441770-3", _at(21))
    ]
