from typing import Protocol

from src.modules.contadores.domain.value_objects.fixed_sum_source_row import FixedSumSourceRow


class FixedSumWorkbookReader(Protocol):
    def read(self, file_path: str) -> list[FixedSumSourceRow]: ...
