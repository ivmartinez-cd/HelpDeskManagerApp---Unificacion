from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class CounterReading:
    """Una lectura de contador de impresora en una fecha dada."""

    fecha: date
    contador: int
    tipo_contador: str
