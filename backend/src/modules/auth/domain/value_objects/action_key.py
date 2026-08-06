import re
from dataclasses import dataclass

from src.modules.auth.domain.errors import InvalidActionKeyError

_KEY_FORMAT = re.compile(r"^[a-z][a-z0-9-]{1,39}$")


@dataclass(frozen=True, slots=True)
class ActionKey:
    """Mismo formato que el CHECK de la tabla action (ver ADR-005)."""

    value: str

    def __post_init__(self) -> None:
        if not _KEY_FORMAT.match(self.value):
            raise InvalidActionKeyError(self.value)
