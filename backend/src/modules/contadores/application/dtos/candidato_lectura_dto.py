from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class CandidatoLecturaDto:
    fecha: date
    tipo_toma: int
    valor: float
    valido: bool
    motivo_invalidez: str | None
