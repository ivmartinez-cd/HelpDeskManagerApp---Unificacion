from pydantic import BaseModel, ConfigDict, Field

from src.modules.auth.domain.value_objects.module_catalog_entry import ModuleCatalogEntry


class ModuleCatalogResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key: str
    label: str
    route: str
    icon: str
    sort_order: int = Field(serialization_alias="sortOrder")
    is_enabled: bool = Field(serialization_alias="isEnabled")

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
