from typing import Protocol

from src.modules.auth.domain.value_objects.feature_catalog_entry import FeatureCatalogEntry


class FeatureCatalogRepository(Protocol):
    async def list_all(self) -> list[FeatureCatalogEntry]: ...
