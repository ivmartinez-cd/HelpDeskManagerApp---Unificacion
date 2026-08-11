"""Implementación Postgres del puerto RequestAlertRepository."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.request_alert import (
    STATE_ACKNOWLEDGED,
    STATE_ESCALATED,
    STATE_TRIGGERED,
    RequestAlert,
)
from src.modules.insumos.infrastructure.models.request_alert_model import RequestAlertModel


class SqlAlchemyRequestAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def escalate_due(self, cutoff: datetime) -> int:
        stmt = (
            update(RequestAlertModel)
            .where(
                RequestAlertModel.state == STATE_TRIGGERED,
                RequestAlertModel.requested_at.is_not(None),
                RequestAlertModel.requested_at <= cutoff,
            )
            .values(state=STATE_ESCALATED, escalated_at=func.now(), updated_at=func.now())
            .returning(RequestAlertModel.hp_request_id)
        )
        return len((await self._session.execute(stmt)).scalars().all())

    async def list_escalated(self) -> list[RequestAlert]:
        stmt = (
            select(RequestAlertModel)
            .where(RequestAlertModel.state == STATE_ESCALATED)
            .order_by(RequestAlertModel.escalated_at.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def acknowledge(self, hp_request_ids: Sequence[int]) -> int:
        if not hp_request_ids:
            return 0
        stmt = (
            update(RequestAlertModel)
            .where(
                RequestAlertModel.hp_request_id.in_(hp_request_ids),
                RequestAlertModel.state == STATE_ESCALATED,
            )
            .values(
                state=STATE_ACKNOWLEDGED, acknowledged_at=func.now(), updated_at=func.now()
            )
            .returning(RequestAlertModel.hp_request_id)
        )
        return len((await self._session.execute(stmt)).scalars().all())


def _to_entity(row: RequestAlertModel) -> RequestAlert:
    return RequestAlert(
        hp_request_id=row.hp_request_id,
        customer_id=row.customer_id,
        customer_name=row.customer_name,
        device_serial=row.device_serial,
        sku=row.sku,
        description=row.description,
        requested_at=row.requested_at,
        first_seen_at=row.first_seen_at,
        escalated_at=row.escalated_at,
    )
