from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FixedSumSourceRow:
    serie: str
    estado: str
    contador_actual: int
