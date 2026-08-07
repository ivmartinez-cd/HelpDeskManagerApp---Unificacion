import re
from dataclasses import dataclass

from src.shared.domain.errors import InvalidModuleKeyError

_KEY_FORMAT = re.compile(r"^[a-z][a-z0-9-]{1,39}$")


@dataclass(frozen=True, slots=True)
class ModuleKey:
    """Mismo formato que el CHECK de la tabla module (ver ADR-005). Vive en
    shared/ porque todo módulo de negocio lo necesita para declarar sus
    propios permisos (ver ADR-007) — no es un concepto propio de auth."""

    value: str

    def __post_init__(self) -> None:
        if not _KEY_FORMAT.match(self.value):
            raise InvalidModuleKeyError(self.value)
