from dataclasses import dataclass

from src.shared.domain.value_objects.feature_key import FeatureKey
from src.shared.domain.value_objects.module_key import ModuleKey


@dataclass(frozen=True, slots=True)
class FeatureCatalogEntry:
    """Fila de `module_feature` (ADR-032): una pantalla/card de un módulo que
    se concede por usuario. La grilla de permisos las muestra debajo de las
    acciones del módulo."""

    key: FeatureKey
    module: ModuleKey
    label: str
    description: str
    sort_order: int
