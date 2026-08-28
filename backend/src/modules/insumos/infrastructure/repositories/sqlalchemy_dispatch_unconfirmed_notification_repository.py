"""Implementación Postgres del puerto DispatchUnconfirmedNotificationRepository."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.infrastructure.models.dispatch_unconfirmed_notification_model import (
    DispatchUnconfirmedNotificationModel,
)


class SqlAlchemyDispatchUnconfirmedNotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_notified_ids(self, hp_request_ids: list[int]) -> set[int]:
        if not hp_request_ids:
            return set()
        stmt = select(DispatchUnconfirmedNotificationModel.hp_request_id).where(
            DispatchUnconfirmedNotificationModel.hp_request_id.in_(hp_request_ids)
        )
        return set((await self._session.execute(stmt)).scalars().all())

    async def mark_notified(self, hp_request_ids: list[int]) -> None:
        if not hp_request_ids:
            return
        stmt = pg_insert(DispatchUnconfirmedNotificationModel).values(
            [{"hp_request_id": rid} for rid in hp_request_ids]
        )
        await self._session.execute(stmt.on_conflict_do_nothing())
        await self._session.flush()
