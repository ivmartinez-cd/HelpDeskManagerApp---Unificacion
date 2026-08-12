"""Tests de integración de SqlAlchemyMailLogRepository (Postgres de test)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.mail_log_entry import MailLogRecord
from src.modules.insumos.infrastructure.repositories.sqlalchemy_mail_log_repository import (
    SqlAlchemyMailLogRepository,
)


def _record(kind: str = "poller_alert", success: bool = True) -> MailLogRecord:
    return MailLogRecord(
        kind=kind,
        recipients="logistica@example.com,otra@example.com",
        subject="Asunto de prueba",
        success=success,
        error=None if success else "b@example.com: SMTP timeout",
    )


async def test_record_y_list_latest_ida_y_vuelta_con_sent_at_poblado(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyMailLogRepository(db_session)
    await repo.record(_record())

    entries = await repo.list_latest(limit=10)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.kind == "poller_alert"
    assert entry.recipients == "logistica@example.com,otra@example.com"
    assert entry.subject == "Asunto de prueba"
    assert entry.success is True
    assert entry.error is None
    assert entry.sent_at is not None


async def test_record_de_un_fallo_guarda_el_error(db_session: AsyncSession) -> None:
    repo = SqlAlchemyMailLogRepository(db_session)
    await repo.record(_record(kind="pending_order_alert", success=False))

    entries = await repo.list_latest(limit=10)

    assert entries[0].success is False
    assert entries[0].error == "b@example.com: SMTP timeout"


async def test_count(db_session: AsyncSession) -> None:
    repo = SqlAlchemyMailLogRepository(db_session)
    assert await repo.count() == 0

    await repo.record(_record())
    await repo.record(_record())

    assert await repo.count() == 2


async def test_list_latest_ordena_por_id_desc(db_session: AsyncSession) -> None:
    repo = SqlAlchemyMailLogRepository(db_session)
    for i in range(3):
        await repo.record(_record(kind=f"kind_{i}"))

    entries = await repo.list_latest(limit=10)

    assert [e.kind for e in entries] == ["kind_2", "kind_1", "kind_0"]
