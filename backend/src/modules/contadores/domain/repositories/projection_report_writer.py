from dataclasses import dataclass
from datetime import date
from typing import Protocol

from src.modules.contadores.domain.value_objects.audit_entry import AuditEntry
from src.modules.contadores.domain.value_objects.counter_projection_result import (
    CounterProjectionResult,
)
from src.modules.contadores.domain.value_objects.projection_summary import ProjectionSummary
from src.modules.contadores.domain.value_objects.siges_row import SigesRow


@dataclass(frozen=True, slots=True)
class ProjectionReportPaths:
    excel_path: str
    siges_csv_path: str


class ProjectionReportWriter(Protocol):
    """Puerto: escribe el Excel completo (Proyección/SiGes/Validación/
    Auditoría/KPIs/Leyenda) y el CSV de SiGes. Implementación concreta con
    openpyxl vive en infrastructure."""

    def write(
        self,
        *,
        results: list[CounterProjectionResult],
        audit: list[AuditEntry],
        siges_rows: list[SigesRow],
        summary: ProjectionSummary,
        fecha_toma: date,
        source_filename: str,
        output_dir: str,
    ) -> ProjectionReportPaths: ...
