from typing import Protocol

from src.modules.contadores.domain.value_objects.fixed_sum_result_row import FixedSumResultRow


class FixedSumCsvWriter(Protocol):
    def write(self, rows: list[FixedSumResultRow], *, output_dir: str, base_name: str) -> str: ...
