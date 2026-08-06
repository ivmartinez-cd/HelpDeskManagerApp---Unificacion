from dataclasses import dataclass

from src.modules.auth.domain.repositories.module_catalog_repository import (
    ModuleCatalogRepository,
)
from src.modules.auth.domain.value_objects.action_catalog_entry import ActionCatalogEntry


@dataclass(frozen=True, slots=True)
class ListActionCatalogDependencies:
    catalog: ModuleCatalogRepository


class ListActionCatalog:
    def __init__(self, deps: ListActionCatalogDependencies) -> None:
        self._deps = deps

    async def execute(self) -> list[ActionCatalogEntry]:
        return await self._deps.catalog.list_actions()
