"""Implementación Postgres del puerto KnownDeviceRepository (tabla known_devices)."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.infrastructure.models.known_device_model import KnownDeviceModel

MONITORED = "Y"


class SqlAlchemyKnownDeviceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_monitored_by_customer(self) -> dict[int, int]:
        stmt = (
            select(KnownDeviceModel.customer_id, func.count())
            .where(KnownDeviceModel.monitor_status == MONITORED)
            .group_by(KnownDeviceModel.customer_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {customer_id: total for customer_id, total in rows}
