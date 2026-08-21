import re
from dataclasses import dataclass

from src.shared.domain.errors import ValidationError

_KEY_FORMAT = re.compile(r"^[a-z][a-z0-9-]{1,59}$")


@dataclass(frozen=True, slots=True)
class FeatureKey:
    """Clave de una "función" del catálogo de permisos (ADR-032): una pantalla
    o card concreta de un módulo que se concede por usuario, además de las
    acciones (ver/crear/…). Vive en `shared/` por el mismo motivo que
    `ModuleKey` (ADR-007): cualquier módulo la declara en su
    `well_known_features.py` y la exige con `require_feature`."""

    value: str

    def __post_init__(self) -> None:
        if not _KEY_FORMAT.match(self.value):
            raise ValidationError(f"Clave de función inválida: {self.value!r}")
