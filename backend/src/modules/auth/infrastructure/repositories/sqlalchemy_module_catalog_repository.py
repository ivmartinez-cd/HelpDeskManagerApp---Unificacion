from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.value_objects.action_catalog_entry import ActionCatalogEntry
from src.modules.auth.domain.value_objects.action_key import ActionKey
from src.modules.auth.domain.value_objects.module_catalog_entry import ModuleCatalogEntry
from src.modules.auth.domain.value_objects.module_key import ModuleKey
from src.modules.auth.infrastructure.models.permission_models import Action, Module, ModuleAction


class SqlAlchemyModuleCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[ModuleCatalogEntry]:
        stmt = select(Module).order_by(Module.sort_order)
        rows = (await self._session.execute(stmt)).scalars().all()
        actions_by_module = await self._actions_by_module()
        return [_to_entry(row, actions_by_module.get(row.key, frozenset())) for row in rows]

    async def list_actions(self) -> list[ActionCatalogEntry]:
        rows = (await self._session.execute(select(Action))).scalars().all()
        return [ActionCatalogEntry(key=ActionKey(row.key), label=row.label) for row in rows]

    async def is_enabled(self, module: ModuleKey) -> bool:
        row = await self._session.get(Module, module.value)
        return row is not None and row.is_enabled

    async def _actions_by_module(self) -> dict[str, frozenset[ActionKey]]:
        stmt = select(ModuleAction.module_key, ModuleAction.action_key)
        rows = (await self._session.execute(stmt)).all()
        grouped: dict[str, set[ActionKey]] = {}
        for module_key, action_key in rows:
            grouped.setdefault(module_key, set()).add(ActionKey(action_key))
        return {key: frozenset(value) for key, value in grouped.items()}


def _to_entry(model: Module, actions: frozenset[ActionKey]) -> ModuleCatalogEntry:
    return ModuleCatalogEntry(
        key=ModuleKey(model.key),
        label=model.label,
        route=model.route,
        icon=model.icon,
        sort_order=model.sort_order,
        is_enabled=model.is_enabled,
        actions=actions,
    )
