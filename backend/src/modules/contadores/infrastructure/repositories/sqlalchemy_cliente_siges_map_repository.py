from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.infrastructure.models.cliente_siges_map_model import (
    ClienteSigesMapModel,
)


class SqlAlchemyClienteSigesMapRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> dict[str, list[int]]:
        rows = await self._session.execute(select(ClienteSigesMapModel))
        alias: dict[str, list[int]] = {}
        for m in rows.scalars():
            alias.setdefault(m.cliente_gestion, []).append(m.siges_empresa_id)
        return alias

    async def replace(self, cliente_gestion: str, siges_empresa_ids: list[int]) -> None:
        await self._session.execute(
            delete(ClienteSigesMapModel).where(
                ClienteSigesMapModel.cliente_gestion == cliente_gestion
            )
        )
        for empresa_id in dict.fromkeys(siges_empresa_ids):
            self._session.add(
                ClienteSigesMapModel(
                    cliente_gestion=cliente_gestion, siges_empresa_id=empresa_id
                )
            )
        await self._session.flush()
