from dataclasses import dataclass, field

from src.shared.domain.value_objects.feature_key import FeatureKey


@dataclass(frozen=True, slots=True)
class FeatureSet:
    """Las funciones (pantallas/cards) concedidas a un usuario. Fail-closed:
    lo que no está, no se tiene. Superadmin se resuelve en presentation
    (`require_feature`), no acá — igual que `PermissionSet`."""

    granted: frozenset[FeatureKey] = field(default_factory=frozenset)

    def has(self, key: FeatureKey) -> bool:
        return key in self.granted
