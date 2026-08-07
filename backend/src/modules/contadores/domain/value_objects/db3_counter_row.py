from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Db3CounterRow:
    """Una fila cruda de la tabla `counters` de un archivo DB3 (SQLite)."""

    serial_number: str
    read_date: date
    read_value: int
    model: str
    counter_class_id: int
