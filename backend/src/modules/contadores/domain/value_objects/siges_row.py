from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class SigesRow:
    """Una fila del CSV que se importa al sistema de facturación SiGes.
    `contador_10`/`contador_20` quedan `""` cuando el equipo no tiene esa
    clase — mismo formato que el CSV de la app vieja."""

    serie: str
    fecha: date
    tipo: int
    clase_10: str
    contador_10: int | str
    clase_20: str
    contador_20: int | str
    motivo: str
    observaciones: str
