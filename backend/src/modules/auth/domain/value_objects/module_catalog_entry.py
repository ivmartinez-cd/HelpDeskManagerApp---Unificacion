from dataclasses import dataclass

from src.modules.auth.domain.value_objects.module_key import ModuleKey


@dataclass(frozen=True, slots=True)
class ModuleCatalogEntry:
    key: ModuleKey
    label: str
    route: str
    icon: str
    sort_order: int
    is_enabled: bool
