from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DecisionOperadorDto:
    pendiente: bool = False
    nota: str | None = None
