import re
from dataclasses import dataclass

from src.modules.auth.domain.errors import InvalidModuleKeyError

_KEY_FORMAT = re.compile(r"^[a-z][a-z0-9-]{1,39}$")


@dataclass(frozen=True, slots=True)
class ModuleKey:
    """Mismo formato que el CHECK de la tabla module (ver ADR-005)."""

    value: str

    def __post_init__(self) -> None:
        if not _KEY_FORMAT.match(self.value):
            raise InvalidModuleKeyError(self.value)
