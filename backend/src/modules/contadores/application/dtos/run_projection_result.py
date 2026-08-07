from dataclasses import dataclass

from src.modules.contadores.domain.value_objects.counter_projection_result import (
    CounterProjectionResult,
)
from src.modules.contadores.domain.value_objects.projection_summary import ProjectionSummary


@dataclass(frozen=True, slots=True)
class RunProjectionResult:
    summary: ProjectionSummary
    results: list[CounterProjectionResult]
    excel_path: str
    siges_csv_path: str
