from typing import Protocol

from src.modules.auth.domain.value_objects.module_catalog_entry import ModuleCatalogEntry
from src.modules.auth.domain.value_objects.module_key import ModuleKey


class ModuleCatalogRepository(Protocol):
    async def list_all(self) -> list[ModuleCatalogEntry]: ...
    async def is_enabled(self, module: ModuleKey) -> bool: ...
