from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PasswordHash:
    """Wrapper de tipo para no confundir un hash con un password en texto plano."""

    value: str
