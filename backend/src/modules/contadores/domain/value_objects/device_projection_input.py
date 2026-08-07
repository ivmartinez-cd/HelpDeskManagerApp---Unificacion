from dataclasses import dataclass
from datetime import date

from src.modules.contadores.domain.value_objects.counter_reading import CounterReading


@dataclass(frozen=True, slots=True)
class DeviceProjectionInput:
    """Todas las lecturas de un equipo (serie+clase) a proyectar hacia
    `fecha_toma` — agrupado en un objeto en vez de pasar 6 parámetros
    sueltos por función (ARCHITECTURE_GUIDE.md §4)."""

    serie: str
    clase: str
    articulo: str
    sector: str
    readings: list[CounterReading]
    fecha_toma: date
