from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class LecturaRef:
    """Una lectura de contador citada como Partida, Llegada, T4 o último
    facturado — valor + fecha + tipo de toma SiGes (ver REGLAS_DE_NEGOCIO §4)."""

    valor: float
    fecha: date
    tipo_toma: int
