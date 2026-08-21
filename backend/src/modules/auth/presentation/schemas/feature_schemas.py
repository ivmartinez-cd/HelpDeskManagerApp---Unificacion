from pydantic import BaseModel, ConfigDict, Field

from src.modules.auth.domain.value_objects.feature_catalog_entry import FeatureCatalogEntry
from src.modules.auth.domain.value_objects.feature_set import FeatureSet
from src.shared.domain.value_objects.feature_key import FeatureKey


class FeatureCatalogResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    key: str
    module: str
    label: str
    description: str
    sort_order: int = Field(serialization_alias="sortOrder")

    @classmethod
    def from_domain(cls, entry: FeatureCatalogEntry) -> "FeatureCatalogResponse":
        return cls(
            key=entry.key.value,
            module=entry.module.value,
            label=entry.label,
            description=entry.description,
            sort_order=entry.sort_order,
        )


class FeaturesResponse(BaseModel):
    features: list[str]

    @classmethod
    def from_domain(cls, features: FeatureSet) -> "FeaturesResponse":
        return cls(features=sorted(f.value for f in features.granted))


class ReplaceFeaturesRequest(BaseModel):
    features: list[str]

    def to_domain(self) -> FeatureSet:
        return FeatureSet(frozenset(FeatureKey(f) for f in self.features))
