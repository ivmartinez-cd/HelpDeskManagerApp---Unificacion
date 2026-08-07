from src.modules.contadores.application.dtos.run_projection_request import RunProjectionRequest
from src.modules.contadores.application.dtos.run_projection_result import RunProjectionResult
from src.modules.contadores.domain.repositories.counter_workbook_reader import (
    CounterWorkbookReader,
)
from src.modules.contadores.domain.repositories.projection_report_writer import (
    ProjectionReportWriter,
)
from src.modules.contadores.domain.services.counter_projector import project_device_counter
from src.modules.contadores.domain.services.projection_summarizer import summarize
from src.modules.contadores.domain.services.siges_export_builder import build_siges_rows
from src.modules.contadores.domain.value_objects.audit_entry import AuditEntry
from src.modules.contadores.domain.value_objects.counter_projection_result import (
    CounterProjectionResult,
)
from src.modules.contadores.domain.value_objects.device_projection_input import (
    DeviceProjectionInput,
)
from src.modules.contadores.domain.value_objects.device_readings import DeviceReadings


class RunCounterProjectionUseCase:
    """Orquesta el algoritmo de dominio sobre cada equipo del archivo de
    entrada y delega la escritura de reportes a infrastructure."""

    def __init__(self, reader: CounterWorkbookReader, writer: ProjectionReportWriter) -> None:
        self._reader = reader
        self._writer = writer

    def execute(self, request: RunProjectionRequest) -> RunProjectionResult:
        devices = self._reader.read(request.file_path)
        results, audit = _project_all_devices(devices, request)
        summary = summarize(results)
        siges_rows = build_siges_rows(results)
        paths = self._writer.write(
            results=results,
            audit=audit,
            siges_rows=siges_rows,
            summary=summary,
            fecha_toma=request.fecha_toma,
            source_filename=request.source_filename,
            output_dir=request.output_dir,
        )
        return RunProjectionResult(
            summary=summary,
            results=results,
            excel_path=paths.excel_path,
            siges_csv_path=paths.siges_csv_path,
        )


def _project_all_devices(
    devices: list[DeviceReadings], request: RunProjectionRequest
) -> tuple[list[CounterProjectionResult], list[AuditEntry]]:
    results: list[CounterProjectionResult] = []
    audit: list[AuditEntry] = []
    for device_readings in devices:
        device_input = DeviceProjectionInput(
            serie=device_readings.serie,
            clase=device_readings.clase,
            articulo=device_readings.articulo,
            sector=device_readings.sector,
            readings=device_readings.readings,
            fecha_toma=request.fecha_toma,
        )
        result, entries = project_device_counter(device_input, request.settings)
        results.append(result)
        audit.extend(entries)
    return results, audit
