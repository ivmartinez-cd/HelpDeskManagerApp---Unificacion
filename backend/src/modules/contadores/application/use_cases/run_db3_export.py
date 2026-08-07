from src.modules.contadores.application.dtos.run_db3_export_request import RunDb3ExportRequest
from src.modules.contadores.application.dtos.run_db3_export_result import RunDb3ExportResult
from src.modules.contadores.domain.errors import EmptyDb3ExportError
from src.modules.contadores.domain.repositories.db3_csv_writer import Db3CsvWriter
from src.modules.contadores.domain.repositories.db3_file_reader import Db3FileReader
from src.modules.contadores.domain.services.db3_export_builder import build_db3_export_rows


class RunDb3ExportUseCase:
    def __init__(self, reader: Db3FileReader, writer: Db3CsvWriter) -> None:
        self._reader = reader
        self._writer = writer

    def execute(self, request: RunDb3ExportRequest) -> RunDb3ExportResult:
        outcome = self._reader.read(request.file_paths)
        if not outcome.rows:
            raise EmptyDb3ExportError(outcome.warnings)

        export_rows = build_db3_export_rows(outcome.rows, request.fecha_maxima)
        csv_path = self._writer.write(
            export_rows, output_dir=request.output_dir, base_name=request.base_name
        )
        return RunDb3ExportResult(
            csv_path=csv_path, warnings=outcome.warnings, row_count=len(export_rows)
        )
