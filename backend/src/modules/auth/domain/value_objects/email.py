import re
from dataclasses import dataclass

from src.modules.auth.domain.errors import InvalidEmailError

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Email:
    """Normaliza a minúsculas — mismo criterio que el auth de VacaSync."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_PATTERN.match(normalized):
            raise InvalidEmailError(self.value)
        object.__setattr__(self, "value", normalized)
