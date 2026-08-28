"""Implementación Postgres del puerto DismissedSupplyRepository."""

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.entities.dismissed_supply import DismissedSupply
from src.modules.insumos.infrastructure.models.dismissed_supply_model import DismissedSupplyModel


class SqlAlchemyDismissedSupplyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def mark_dismissed(
        self, supply_id: int, device_serial: str, hp_request_id: int | None = None
    ) -> None:
        stmt = pg_insert(DismissedSupplyModel).values(
            supply_id=supply_id, device_serial=device_serial, hp_request_id=hp_request_id
        )
        await self._session.execute(stmt.on_conflict_do_nothing())
        await self._session.flush()

    async def get_dismissed_ids(self, supply_ids: list[int]) -> set[int]:
        if not supply_ids:
            return set()
        stmt = select(DismissedSupplyModel.supply_id).where(
            DismissedSupplyModel.supply_id.in_(supply_ids)
        )
        return set((await self._session.execute(stmt)).scalars().all())

    async def get_all_dismissed_ids(self) -> set[int]:
        stmt = select(DismissedSupplyModel.supply_id)
        return set((await self._session.execute(stmt)).scalars().all())

    async def get_pending_unignore(self) -> list[DismissedSupply]:
        stmt = select(DismissedSupplyModel).where(DismissedSupplyModel.hp_request_id.is_not(None))
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            DismissedSupply(
                supply_id=r.supply_id,
                device_serial=r.device_serial,
                hp_request_id=r.hp_request_id,
            )
            for r in rows
        ]

    async def clear(self, supply_id: int) -> None:
        stmt = delete(DismissedSupplyModel).where(DismissedSupplyModel.supply_id == supply_id)
        await self._session.execute(stmt)
        await self._session.flush()
