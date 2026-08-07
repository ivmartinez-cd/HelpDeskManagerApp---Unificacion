from dataclasses import dataclass

from src.modules.contadores.domain.value_objects.counter_reading import CounterReading


@dataclass(frozen=True, slots=True)
class DeviceReadings:
    """Todas las lecturas de un equipo (serie+clase) tal como vienen del
    archivo de entrada, sin `fecha_toma` — eso lo agrega el caso de uso."""

    serie: str
    clase: str
    articulo: str
    sector: str
    readings: list[CounterReading]
