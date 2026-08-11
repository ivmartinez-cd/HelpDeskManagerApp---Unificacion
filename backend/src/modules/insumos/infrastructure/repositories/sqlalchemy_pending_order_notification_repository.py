"""Implementación Postgres de PendingOrderNotificationRepository."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.infrastructure.models.pending_order_notification_model import (
    PendingOrderNotificationModel,
)


class SqlAlchemyPendingOrderNotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_notified_ids(self, hp_request_ids: list[int]) -> set[int]:
        if not hp_request_ids:
            return set()
        rows = await self._session.scalars(
            select(PendingOrderNotificationModel.hp_request_id).where(
                PendingOrderNotificationModel.hp_request_id.in_(hp_request_ids)
            )
        )
        return set(rows.all())

    async def mark_notified(self, hp_request_ids: list[int]) -> None:
        if not hp_request_ids:
            return
        stmt = pg_insert(PendingOrderNotificationModel).values(
            [{"hp_request_id": rid} for rid in hp_request_ids]
        )
        await self._session.execute(stmt.on_conflict_do_nothing())
