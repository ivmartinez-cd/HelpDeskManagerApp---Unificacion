from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.value_objects.module_catalog_entry import ModuleCatalogEntry
from src.modules.auth.domain.value_objects.module_key import ModuleKey
from src.modules.auth.infrastructure.models.permission_models import Module


class SqlAlchemyModuleCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[ModuleCatalogEntry]:
        stmt = select(Module).order_by(Module.sort_order)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entry(row) for row in rows]

    async def is_enabled(self, module: ModuleKey) -> bool:
        row = await self._session.get(Module, module.value)
        return row is not None and row.is_enabled


def _to_entry(model: Module) -> ModuleCatalogEntry:
    return ModuleCatalogEntry(
        key=ModuleKey(model.key),
        label=model.label,
        route=model.route,
        icon=model.icon,
        sort_order=model.sort_order,
        is_enabled=model.is_enabled,
    )
