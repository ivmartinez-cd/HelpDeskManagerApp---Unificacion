"""Implementación Postgres del puerto RequestAlertRepository."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import case, func, null, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.request_alert import (
    STATE_ACKNOWLEDGED,
    STATE_ESCALATED,
    STATE_RESOLVED,
    STATE_TRIGGERED,
    AlertPendingEntry,
    RequestAlert,
)
from src.modules.insumos.infrastructure.models.request_alert_model import RequestAlertModel


class SqlAlchemyRequestAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def sync_pending(self, pending: list[AlertPendingEntry]) -> None:
        if pending:
            rows = [
                {
                    "hp_request_id": e.hp_request_id,
                    "customer_id": e.customer_id,
                    "customer_name": e.customer_name,
                    "device_serial": e.device_serial,
                    "sku": e.sku,
                    "description": e.description,
                    "requested_at": e.requested_at,
                    "state": STATE_TRIGGERED,
                    "updated_at": func.now(),
                }
                for e in pending
            ]
            stmt = pg_insert(RequestAlertModel).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["hp_request_id"],
                set_={
                    "customer_id": stmt.excluded.customer_id,
                    "customer_name": stmt.excluded.customer_name,
                    "device_serial": stmt.excluded.device_serial,
                    "sku": stmt.excluded.sku,
                    "description": stmt.excluded.description,
                    "requested_at": stmt.excluded.requested_at,
                    "updated_at": func.now(),
                    "state": case(
                        (RequestAlertModel.state == STATE_RESOLVED, STATE_TRIGGERED),
                        else_=RequestAlertModel.state,
                    ),
                    "first_seen_at": case(
                        (RequestAlertModel.state == STATE_RESOLVED, func.now()),
                        else_=RequestAlertModel.first_seen_at,
                    ),
                    "escalated_at": case(
                        (RequestAlertModel.state == STATE_RESOLVED, null()),
                        else_=RequestAlertModel.escalated_at,
                    ),
                    "acknowledged_at": case(
                        (RequestAlertModel.state == STATE_RESOLVED, null()),
                        else_=RequestAlertModel.acknowledged_at,
                    ),
                    "resolved_at": case(
                        (RequestAlertModel.state == STATE_RESOLVED, null()),
                        else_=RequestAlertModel.resolved_at,
                    ),
                },
            )
            await self._session.execute(stmt)
        pending_ids = {e.hp_request_id for e in pending}
        active_ids = set(
            (
                await self._session.scalars(
                    select(RequestAlertModel.hp_request_id).where(
                        RequestAlertModel.state != STATE_RESOLVED
                    )
                )
            ).all()
        )
        to_resolve = active_ids - pending_ids
        if to_resolve:
            await self._session.execute(
                update(RequestAlertModel)
                .where(RequestAlertModel.hp_request_id.in_(to_resolve))
                .values(state=STATE_RESOLVED, resolved_at=func.now(), updated_at=func.now())
            )

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
