from dataclasses import dataclass

from src.modules.auth.domain.repositories.module_catalog_repository import (
    ModuleCatalogRepository,
)
from src.modules.auth.domain.value_objects.module_catalog_entry import ModuleCatalogEntry


@dataclass(frozen=True, slots=True)
class ListModuleCatalogDependencies:
    catalog: ModuleCatalogRepository


class ListModuleCatalog:
    def __init__(self, deps: ListModuleCatalogDependencies) -> None:
        self._deps = deps

    async def execute(self) -> list[ModuleCatalogEntry]:
        return await self._deps.catalog.list_all()
