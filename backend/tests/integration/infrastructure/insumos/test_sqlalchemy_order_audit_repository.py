"""Tests de integración de SqlAlchemyOrderAuditRepository (Postgres de test)."""

from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CANCELLED,
    EVENT_CREATED,
    EVENT_FAILED,
    AuditRecord,
    AuditSnapshot,
)
from src.modules.insumos.domain.value_objects.audit_history import AuditFilters
from src.modules.insumos.infrastructure.models.order_audit_model import OrderAuditModel
from src.modules.insumos.infrastructure.repositories.sqlalchemy_order_audit_repository import (
    SqlAlchemyOrderAuditRepository,
)

_NO_FILTERS = AuditFilters()


def _created(hp_request_id: int = 974325, dry_run: bool = False) -> AuditRecord:
    return AuditRecord(
        event=EVENT_CREATED,
        hp_request_id=hp_request_id,
        customer_id=8,
        customer_name="Cliente Test",
        device_serial="SERIE1",
        sku="CF230A",
        internal_order_id="441770-3",
        dry_run=dry_run,
    )


async def _insert_at(db_session: AsyncSession, created_at: datetime, **overrides: object) -> None:
    """Inserta un OrderAuditModel directo (con `created_at` elegido a mano) —
    AuditRecord no tiene ese campo porque `created_at` tiene server_default."""
    values: dict[str, object] = {
        "event": EVENT_CREATED,
        "hp_request_id": 974325,
        "customer_id": 8,
        "created_at": created_at,
    }
    values.update(overrides)
    db_session.add(OrderAuditModel(**values))
    await db_session.flush()


async def test_count_created_today_cuenta_solo_creados_reales_de_hoy(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    await repo.record(_created())
    await repo.record(_created())
    # Ninguno de estos debe contar: dry-run, otro evento, otra solicitud.
    await repo.record(_created(dry_run=True))
    await repo.record(AuditRecord(event=EVENT_FAILED, hp_request_id=974325))
    await repo.record(_created(hp_request_id=111111))

    assert await repo.count_created_today(974325) == 2


async def test_count_created_today_sin_eventos_es_cero(db_session: AsyncSession) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    assert await repo.count_created_today(974325) == 0


async def test_list_page_pagina_mas_reciente_primero(db_session: AsyncSession) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    for i in range(5):
        await repo.record(_created(hp_request_id=974000 + i))

    assert await repo.count(_NO_FILTERS) == 5
    first_page = await repo.list_page(_NO_FILTERS, limit=2, offset=0)
    assert [r.hp_request_id for r in first_page] == [974004, 974003]
    second_page = await repo.list_page(_NO_FILTERS, limit=2, offset=2)
    assert [r.hp_request_id for r in second_page] == [974002, 974001]
    assert first_page[0].audit_id > second_page[0].audit_id
    assert first_page[0].created_at is not None
    assert first_page[0].event == EVENT_CREATED


async def test_backfill_snapshots_completa_filas_existentes(db_session: AsyncSession) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    await repo.record(_created())
    stored = (await repo.list_page(_NO_FILTERS, limit=1, offset=0))[0]
    assert stored.device_id is None

    await repo.backfill_snapshots(
        [
            AuditSnapshot(
                audit_id=stored.audit_id,
                device_id=7,
                initial_percent_left=12,
                initial_days_left=3,
            )
        ]
    )

    db_session.expire_all()  # el backfill va por Core: refrescar el identity map
    updated = (await repo.list_page(_NO_FILTERS, limit=1, offset=0))[0]
    assert updated.device_id == 7
    assert updated.initial_percent_left == 12
    assert updated.initial_days_left == 3


async def test_filtro_por_multiples_eventos(db_session: AsyncSession) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    await repo.record(_created(hp_request_id=1))
    await repo.record(AuditRecord(event=EVENT_FAILED, hp_request_id=2))
    await repo.record(AuditRecord(event=EVENT_CANCELLED, hp_request_id=3))

    filters = AuditFilters(events=(EVENT_CREATED, EVENT_FAILED))
    rows = await repo.list_page(filters, limit=10, offset=0)

    assert {r.event for r in rows} == {EVENT_CREATED, EVENT_FAILED}
    assert await repo.count(filters) == 2


async def test_evento_fuera_del_filtro_no_matchea_tupla_vacia(db_session: AsyncSession) -> None:
    """events=() (intersección imposible, ver events_for_scope) trae 0 filas,
    no "sin filtro"."""
    repo = SqlAlchemyOrderAuditRepository(db_session)
    await repo.record(_created())

    filters = AuditFilters(events=())
    assert await repo.count(filters) == 0
    assert await repo.list_page(filters, limit=10, offset=0) == []


async def test_rango_en_el_borde_del_dia_argentino(db_session: AsyncSession) -> None:
    """02:00 UTC de un día X es, en huso argentino (UTC-3), las 23:00 del día
    calendario X-1 — el filtro tiene que usar el día argentino, no el UTC."""
    repo = SqlAlchemyOrderAuditRepository(db_session)
    dia_x = date(2026, 8, 12)
    dia_x_menos_1 = date(2026, 8, 11)
    momento_utc = datetime(2026, 8, 12, 2, 0, 0, tzinfo=UTC)
    await _insert_at(db_session, momento_utc)

    filtro_dia_previo = AuditFilters(start_day=dia_x_menos_1, end_day=dia_x_menos_1)
    filtro_dia_x = AuditFilters(start_day=dia_x, end_day=dia_x)

    assert await repo.count(filtro_dia_previo) == 1
    assert await repo.count(filtro_dia_x) == 0


async def test_busqueda_en_las_6_columnas_case_insensitive_con_null(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    now = datetime.now(UTC)
    await _insert_at(
        db_session,
        now,
        hp_request_id=1,
        customer_name="Cliente ACME",
        device_serial=None,
        sku=None,
        description=None,
        internal_order_id=None,
        detail=None,
    )
    await _insert_at(db_session, now, hp_request_id=2, customer_name="Otro Cliente")

    filters = AuditFilters(search="acme")  # minúsculas, columna en mayúsculas parcial
    rows = await repo.list_page(filters, limit=10, offset=0)

    assert [r.hp_request_id for r in rows] == [1]


async def test_busqueda_con_porcentaje_literal_no_actua_como_wildcard(
    db_session: AsyncSession,
) -> None:
    """Sin escapar, `%` en LIKE matchea cualquier cosa: "50%" sin escape
    encontraría también "501 cupos" (contiene "50" seguido de cualquier
    cosa). Escapado, solo matchea el literal "50%"."""
    repo = SqlAlchemyOrderAuditRepository(db_session)
    now = datetime.now(UTC)
    await _insert_at(db_session, now, hp_request_id=1, detail="Falló: 50% cupo")
    await _insert_at(db_session, now, hp_request_id=2, detail="Falló: 501 cupos")

    filters = AuditFilters(search="50%")
    rows = await repo.list_page(filters, limit=10, offset=0)

    assert [r.hp_request_id for r in rows] == [1]


async def test_count_coherente_con_list_page_sin_paginar(db_session: AsyncSession) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    for i in range(7):
        await repo.record(_created(hp_request_id=974000 + i))

    total = await repo.count(_NO_FILTERS)
    all_rows = await repo.list_page(_NO_FILTERS, limit=1000, offset=0)

    assert total == len(all_rows) == 7


async def test_count_by_event(db_session: AsyncSession) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    await repo.record(_created(hp_request_id=1))
    await repo.record(_created(hp_request_id=2))
    await repo.record(AuditRecord(event=EVENT_FAILED, hp_request_id=3))

    counts = await repo.count_by_event(_NO_FILTERS)

    assert counts == {EVENT_CREATED: 2, EVENT_FAILED: 1}


async def test_closures_for_toma_el_max_id_entre_dos_created(db_session: AsyncSession) -> None:
    """Dos CREATED de la misma solicitud (recarga después de anular): el
    último (mayor id), no cualquiera. Los ids no se comparan contra
    constantes: la secuencia de `id` es global a la tabla y no se resetea
    entre tests (no es transaccional), así que se leen los ids reales."""
    repo = SqlAlchemyOrderAuditRepository(db_session)
    await repo.record(_created(hp_request_id=974325))
    await repo.record(AuditRecord(event=EVENT_CANCELLED, hp_request_id=974325))
    await repo.record(_created(hp_request_id=974325))
    rows = await repo.list_page(AuditFilters(), limit=10, offset=0)
    first_created, cancelled, second_created = sorted(rows, key=lambda r: r.audit_id)

    closures = await repo.closures_for([974325])

    assert closures.last_created[974325] == second_created.audit_id
    assert closures.last_closed[974325] == cancelled.audit_id
    assert second_created.audit_id > first_created.audit_id > 0


async def test_closures_for_con_ids_vacios_no_pega_a_la_bd(db_session: AsyncSession) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    closures = await repo.closures_for([])

    assert closures.last_created == {}
    assert closures.last_closed == {}
