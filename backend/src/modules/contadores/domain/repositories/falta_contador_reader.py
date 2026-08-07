from typing import Protocol

from src.modules.contadores.domain.value_objects.falta_contador_source_row import (
    FaltaContadorSourceRow,
)


class FaltaContadorReader(Protocol):
    def read(self, file_path: str) -> list[FaltaContadorSourceRow]: ...
