from dataclasses import dataclass
from typing import Protocol

from src.modules.contadores.domain.value_objects.db3_counter_row import Db3CounterRow


@dataclass(frozen=True, slots=True)
class Db3ReadOutcome:
    rows: list[Db3CounterRow]
    warnings: list[str]


class Db3FileReader(Protocol):
    """Puerto: lee uno o más archivos DB3 (SQLite). Un archivo con estructura
    inesperada o sin datos no aborta el lote entero — se reporta como
    warning, igual que la app vieja."""

    def read(self, file_paths: list[str]) -> Db3ReadOutcome: ...
