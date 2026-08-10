"""Implementación Postgres del puerto OrderAuditRepository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.audit_record import EVENT_CREATED, AuditRecord
from src.modules.insumos.infrastructure.models.order_audit_model import OrderAuditModel
from src.modules.insumos.infrastructure.repositories._argentina_day import is_today_argentina


class SqlAlchemyOrderAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, entry: AuditRecord) -> None:
        self._session.add(
            OrderAuditModel(
                event=entry.event,
                hp_request_id=entry.hp_request_id,
                customer_id=entry.customer_id,
                customer_name=entry.customer_name,
                device_serial=entry.device_serial,
                sku=entry.sku,
                internal_order_id=entry.internal_order_id,
                detail=entry.detail,
                dry_run=entry.dry_run,
                hp_request_time=entry.hp_request_time,
                description=entry.description,
                device_id=entry.device_id,
                order_type=entry.order_type,
                initial_percent_left=entry.initial_percent_left,
                initial_days_left=entry.initial_days_left,
                initial_pages_left=entry.initial_pages_left,
            )
        )
        await self._session.flush()

    async def count_created_today(self, hp_request_id: int) -> int:
        stmt = select(func.count()).where(
            OrderAuditModel.event == EVENT_CREATED,
            OrderAuditModel.hp_request_id == hp_request_id,
            OrderAuditModel.dry_run.is_(False),
            is_today_argentina(OrderAuditModel.created_at),
        )
        return (await self._session.execute(stmt)).scalar_one()
