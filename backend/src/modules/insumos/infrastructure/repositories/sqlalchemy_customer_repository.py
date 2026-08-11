"""Implementación Postgres del puerto CustomerRepository."""

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.zone_contacts import Customer
from src.modules.insumos.infrastructure.models.customer_config_model import CustomerConfigModel


class SqlAlchemyCustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Customer]:
        stmt = select(CustomerConfigModel).order_by(CustomerConfigModel.name)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [Customer(customer_id=r.customer_id, name=r.name, enabled=r.enabled) for r in rows]

    async def set_enabled(self, customer_id: int, enabled: bool) -> None:
        stmt = (
            update(CustomerConfigModel)
            .where(CustomerConfigModel.customer_id == customer_id)
            .values(enabled=enabled)
        )
        await self._session.execute(stmt)

    async def bulk_toggle(self, enabled: bool) -> None:
        await self._session.execute(update(CustomerConfigModel).values(enabled=enabled))

    async def sync(self, customers: list[dict[str, object]]) -> None:
        if not customers:
            return
        values = [
            {"customer_id": c["customerId"], "name": c["name"], "enabled": False}
            for c in customers
        ]
        stmt = insert(CustomerConfigModel).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["customer_id"],
            set_={"name": stmt.excluded.name},
        )
        await self._session.execute(stmt)
