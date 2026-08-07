from typing import Protocol

from src.modules.contadores.domain.value_objects.estimation_zero_row import EstimationZeroRow


class EstimationZeroWriter(Protocol):
    def write(self, rows: list[EstimationZeroRow], *, output_dir: str, cliente: str) -> str: ...
