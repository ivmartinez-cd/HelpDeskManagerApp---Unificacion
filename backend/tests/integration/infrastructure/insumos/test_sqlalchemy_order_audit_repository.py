"""Tests de integración de SqlAlchemyOrderAuditRepository (Postgres de test)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CREATED,
    EVENT_FAILED,
    AuditRecord,
    AuditSnapshot,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_order_audit_repository import (
    SqlAlchemyOrderAuditRepository,
)


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


async def test_list_latest_pagina_mas_reciente_primero(db_session: AsyncSession) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    for i in range(5):
        await repo.record(_created(hp_request_id=974000 + i))

    assert await repo.count() == 5
    first_page = await repo.list_latest(limit=2)
    assert [r.hp_request_id for r in first_page] == [974004, 974003]
    second_page = await repo.list_latest(limit=2, offset=2)
    assert [r.hp_request_id for r in second_page] == [974002, 974001]
    assert first_page[0].audit_id > second_page[0].audit_id
    assert first_page[0].created_at is not None
    assert first_page[0].event == EVENT_CREATED


async def test_backfill_snapshots_completa_filas_existentes(db_session: AsyncSession) -> None:
    repo = SqlAlchemyOrderAuditRepository(db_session)
    await repo.record(_created())
    stored = (await repo.list_latest(limit=1))[0]
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
    updated = (await repo.list_latest(limit=1))[0]
    assert updated.device_id == 7
    assert updated.initial_percent_left == 12
    assert updated.initial_days_left == 3
