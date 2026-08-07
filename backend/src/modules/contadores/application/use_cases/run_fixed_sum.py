import os

from src.modules.contadores.application.dtos.run_fixed_sum_request import RunFixedSumRequest
from src.modules.contadores.domain.repositories.fixed_sum_csv_writer import FixedSumCsvWriter
from src.modules.contadores.domain.repositories.fixed_sum_workbook_reader import (
    FixedSumWorkbookReader,
)
from src.modules.contadores.domain.services.fixed_sum_builder import build_fixed_sum_rows


class RunFixedSumUseCase:
    """Un CSV de salida por cada archivo de entrada (no se consolidan) —
    mismo comportamiento que `procesar_suma_fija` de la app vieja."""

    def __init__(self, reader: FixedSumWorkbookReader, writer: FixedSumCsvWriter) -> None:
        self._reader = reader
        self._writer = writer

    def execute(self, request: RunFixedSumRequest) -> list[str]:
        return [self._process_one(path, request) for path in request.file_paths]

    def _process_one(self, file_path: str, request: RunFixedSumRequest) -> str:
        source = self._reader.read(file_path)
        rows = build_fixed_sum_rows(source, request.fecha, request.hojas_a_sumar)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        return self._writer.write(rows, output_dir=request.output_dir, base_name=base_name)
