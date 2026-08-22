"""Tests de integración de SqlAlchemyRequestAlertRepository (Postgres de test).

Máquina de estados de request_alerts: TRIGGERED → ESCALATED → ACKNOWLEDGED | RESOLVED,
con reapertura RESOLVED → TRIGGERED cuando la misma solicitud vuelve a estar pendiente.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.request_alert import (
    STATE_ACKNOWLEDGED,
    STATE_ESCALATED,
    STATE_RESOLVED,
    STATE_TRIGGERED,
    AlertPendingEntry,
)
from src.modules.insumos.infrastructure.models.request_alert_model import RequestAlertModel
from src.modules.insumos.infrastructure.repositories.sqlalchemy_request_alert_repository import (
    SqlAlchemyRequestAlertRepository,
)

_NOW = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)


def _pending(hp_request_id: int, requested_at: datetime | None = _NOW) -> AlertPendingEntry:
    return AlertPendingEntry(
        hp_request_id=hp_request_id,
        customer_id=8,
        customer_name="Cliente Test",
        device_serial=f"SERIE{hp_request_id}",
        sku="CF230A",
        description="Toner negro",
        requested_at=requested_at,
    )


async def _rows(db_session: AsyncSession) -> dict[int, RequestAlertModel]:
    # El repo escribe con UPDATE/INSERT crudos: hay que expirar el identity map para
    # que la relectura traiga el estado real y no el cacheado en la sesión.
    db_session.expire_all()
    result = await db_session.execute(select(RequestAlertModel))
    return {row.hp_request_id: row for row in result.scalars().all()}


async def test_sync_pending_inserta_como_triggered(db_session: AsyncSession) -> None:
    repo = SqlAlchemyRequestAlertRepository(db_session)

    await repo.sync_pending([_pending(1), _pending(2)])

    rows = await _rows(db_session)
    assert {hp: r.state for hp, r in rows.items()} == {1: STATE_TRIGGERED, 2: STATE_TRIGGERED}
    assert rows[1].customer_name == "Cliente Test"
    assert rows[1].device_serial == "SERIE1"
    assert rows[1].resolved_at is None


async def test_sync_pending_resuelve_las_que_dejaron_de_estar_pendientes(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyRequestAlertRepository(db_session)
    await repo.sync_pending([_pending(1), _pending(2)])

    await repo.sync_pending([_pending(2)])

    rows = await _rows(db_session)
    assert rows[1].state == STATE_RESOLVED
    assert rows[1].resolved_at is not None
    assert rows[2].state == STATE_TRIGGERED


async def test_sync_pending_vacio_resuelve_todas_las_activas(db_session: AsyncSession) -> None:
    repo = SqlAlchemyRequestAlertRepository(db_session)
    await repo.sync_pending([_pending(1)])

    await repo.sync_pending([])

    rows = await _rows(db_session)
    assert rows[1].state == STATE_RESOLVED


async def test_sync_pending_reabre_una_resuelta_y_limpia_sus_marcas(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyRequestAlertRepository(db_session)
    await repo.sync_pending([_pending(1, requested_at=_NOW - timedelta(hours=5))])
    assert await repo.escalate_due(cutoff=_NOW) == 1
    assert await repo.acknowledge([1]) == 1
    await repo.sync_pending([])  # → RESOLVED con escalated_at/acknowledged_at seteados
    before = (await _rows(db_session))[1]
    assert before.state == STATE_RESOLVED
    first_seen_before = before.first_seen_at

    await repo.sync_pending([_pending(1, requested_at=_NOW)])

    row = (await _rows(db_session))[1]
    assert row.state == STATE_TRIGGERED
    assert row.requested_at == _NOW
    assert row.escalated_at is None
    assert row.acknowledged_at is None
    assert row.resolved_at is None
    assert row.first_seen_at >= first_seen_before


async def test_sync_pending_conserva_el_estado_de_una_escalada_que_sigue_pendiente(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyRequestAlertRepository(db_session)
    await repo.sync_pending([_pending(1, requested_at=_NOW - timedelta(hours=5))])
    await repo.escalate_due(cutoff=_NOW)
    escalated_at = (await _rows(db_session))[1].escalated_at

    await repo.sync_pending([_pending(1, requested_at=_NOW - timedelta(hours=5))])

    row = (await _rows(db_session))[1]
    assert row.state == STATE_ESCALATED
    assert row.escalated_at == escalated_at


async def test_escalate_due_solo_triggered_con_requested_at_vencido(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyRequestAlertRepository(db_session)
    await repo.sync_pending(
        [
            _pending(1, requested_at=_NOW - timedelta(hours=2)),
            _pending(2, requested_at=_NOW + timedelta(hours=2)),
            _pending(3, requested_at=None),
        ]
    )

    assert await repo.escalate_due(cutoff=_NOW) == 1
    # Idempotente: la ya escalada no se vuelve a contar.
    assert await repo.escalate_due(cutoff=_NOW) == 0

    escalated = await repo.list_escalated()
    assert [a.hp_request_id for a in escalated] == [1]
    assert escalated[0].escalated_at is not None
    assert escalated[0].customer_id == 8
    assert escalated[0].sku == "CF230A"


async def test_acknowledge_solo_afecta_escaladas(db_session: AsyncSession) -> None:
    repo = SqlAlchemyRequestAlertRepository(db_session)
    await repo.sync_pending(
        [_pending(1, requested_at=_NOW - timedelta(hours=2)), _pending(2, requested_at=_NOW)]
    )
    await repo.escalate_due(cutoff=_NOW - timedelta(hours=1))

    assert await repo.acknowledge([]) == 0
    assert await repo.acknowledge([1, 2, 99]) == 1

    rows = await _rows(db_session)
    assert rows[1].state == STATE_ACKNOWLEDGED
    assert rows[1].acknowledged_at is not None
    assert rows[2].state == STATE_TRIGGERED
    assert await repo.list_escalated() == []
