from src.modules.contadores.application.dtos.run_estimation_zero_from_proceso_request import (
    RunEstimationZeroFromProcesoRequest,
)
from src.modules.contadores.domain.ports.falta_contador_proceso_port import (
    FaltaContadorProcesoPort,
)
from src.modules.contadores.domain.repositories.estimation_zero_writer import (
    EstimationZeroWriter,
)
from src.modules.contadores.domain.services.estimation_zero_builder import (
    build_estimation_zero_rows,
)


class RunEstimationZeroDesdeProcesoUseCase:
    """Mismo armado que `RunEstimationZeroUseCase`, pero con el origen de
    datos en vivo contra Siges (`Nro_Proceso`) en vez de un CSV subido a
    mano — reusa `build_estimation_zero_rows` como única fuente de verdad
    del filtro/agrupado, para que los dos caminos no puedan divergir."""

    def __init__(self, source: FaltaContadorProcesoPort, writer: EstimationZeroWriter) -> None:
        self._source = source
        self._writer = writer

    async def execute(self, request: RunEstimationZeroFromProcesoRequest) -> str:
        proceso = await self._source.fetch(request.nro_proceso)
        rows = build_estimation_zero_rows(proceso.filas, request.fecha_nueva)
        return self._writer.write(rows, output_dir=request.output_dir, cliente=proceso.cliente)
