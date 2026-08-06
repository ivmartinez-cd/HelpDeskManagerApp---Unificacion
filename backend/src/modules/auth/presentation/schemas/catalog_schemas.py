from pydantic import BaseModel

from src.modules.auth.domain.value_objects.module_catalog_entry import ModuleCatalogEntry


class ModuleCatalogResponse(BaseModel):
    key: str
    label: str
    route: str
    icon: str
    sort_order: int
    is_enabled: bool

    @classmethod
    def from_domain(cls, entry: ModuleCatalogEntry) -> "ModuleCatalogResponse":
        return cls(
            key=entry.key.value,
            label=entry.label,
            route=entry.route,
            icon=entry.icon,
            sort_order=entry.sort_order,
            is_enabled=entry.is_enabled,
        )
