"""Implementación Postgres del puerto MailLogRepository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.mail_log_entry import MailLogEntry
from src.modules.insumos.infrastructure.models.mail_log_model import MailLogModel


class SqlAlchemyMailLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_latest(self, limit: int, offset: int = 0) -> list[MailLogEntry]:
        stmt = (
            select(MailLogModel).order_by(MailLogModel.id.desc()).limit(limit).offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entry(row) for row in rows]

    async def count(self) -> int:
        stmt = select(func.count()).select_from(MailLogModel)
        return (await self._session.execute(stmt)).scalar_one()


def _to_entry(row: MailLogModel) -> MailLogEntry:
    return MailLogEntry(
        entry_id=row.id,
        kind=row.kind,
        recipients=row.recipients,
        subject=row.subject,
        success=row.success,
        error=row.error,
        sent_at=row.sent_at,
    )
