from src.modules.contadores.application.dtos.run_estimation_zero_request import (
    RunEstimationZeroRequest,
)
from src.modules.contadores.domain.repositories.estimation_zero_writer import (
    EstimationZeroWriter,
)
from src.modules.contadores.domain.repositories.falta_contador_reader import FaltaContadorReader
from src.modules.contadores.domain.services.estimation_zero_builder import (
    build_estimation_zero_rows,
)


class RunEstimationZeroUseCase:
    def __init__(self, reader: FaltaContadorReader, writer: EstimationZeroWriter) -> None:
        self._reader = reader
        self._writer = writer

    def execute(self, request: RunEstimationZeroRequest) -> str:
        source = self._reader.read(request.file_path)
        rows = build_estimation_zero_rows(source, request.fecha_nueva)
        return self._writer.write(rows, output_dir=request.output_dir, cliente=request.cliente)
