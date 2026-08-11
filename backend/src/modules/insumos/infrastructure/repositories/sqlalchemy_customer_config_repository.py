"""Implementación Postgres del puerto CustomerConfigRepository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.customer_config import CustomerConfig
from src.modules.insumos.infrastructure.models.customer_config_model import CustomerConfigModel


class SqlAlchemyCustomerConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_enabled(self) -> list[CustomerConfig]:
        stmt = (
            select(CustomerConfigModel)
            .where(CustomerConfigModel.enabled.is_(True))
            .order_by(CustomerConfigModel.name)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            CustomerConfig(customer_id=row.customer_id, name=row.name, enabled=row.enabled)
            for row in rows
        ]

    async def get_names(self) -> dict[int, str]:
        stmt = select(CustomerConfigModel.customer_id, CustomerConfigModel.name)
        rows = (await self._session.execute(stmt)).all()
        return {customer_id: name for customer_id, name in rows}
