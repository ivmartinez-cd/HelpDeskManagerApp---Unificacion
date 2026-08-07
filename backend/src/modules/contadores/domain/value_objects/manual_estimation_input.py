from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ManualEstimationInput:
    contador_inicial: int
    contador_final: int
    fecha_inicial: date
    fecha_final: date
    fecha_estimacion: date
