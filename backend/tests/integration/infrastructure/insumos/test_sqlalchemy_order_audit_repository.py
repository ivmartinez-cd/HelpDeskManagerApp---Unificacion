"""Tests de integración de SqlAlchemyOrderAuditRepository (Postgres de test)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CREATED,
    EVENT_FAILED,
    AuditRecord,
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
