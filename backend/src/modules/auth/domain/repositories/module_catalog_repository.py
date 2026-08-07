from typing import Protocol

from src.modules.auth.domain.value_objects.action_catalog_entry import ActionCatalogEntry
from src.modules.auth.domain.value_objects.module_catalog_entry import ModuleCatalogEntry
from src.shared.domain.value_objects.module_key import ModuleKey


class ModuleCatalogRepository(Protocol):
    async def list_all(self) -> list[ModuleCatalogEntry]: ...
    async def list_actions(self) -> list[ActionCatalogEntry]: ...
    async def is_enabled(self, module: ModuleKey) -> bool: ...
