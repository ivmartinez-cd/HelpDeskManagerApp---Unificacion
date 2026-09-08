from src.modules.contadores.application.dtos.reporte_xlsx_detalle_proceso_dto import (
    AlcanceReporte,
    ReporteXlsxDetalleProceso,
)
from src.modules.contadores.domain.ports.detalle_contador_proceso_port import (
    DetalleContadorProcesoPort,
)
from src.modules.contadores.domain.value_objects.detalle_contador_row import (
    DetalleContadorRow,
)
from src.modules.contadores.infrastructure.xlsx.openpyxl_detalle_contador_writer import (
    OpenpyxlDetalleContadorWriter,
)


class GenerarReporteXlsxDetalleProcesoUseCase:
    def __init__(
        self, port: DetalleContadorProcesoPort, writer: OpenpyxlDetalleContadorWriter
    ) -> None:
        self._port = port
        self._writer = writer

    async def execute(self, nro_proceso: int, alcance: AlcanceReporte) -> ReporteXlsxDetalleProceso:
        detalle = await self._port.fetch(nro_proceso)
        filas = _filtrar(detalle.filas, alcance)
        contenido = self._writer.write(filas, detalle.cliente, nro_proceso)
        sufijo = "FaltaContador" if alcance == "falta_contador" else "Completo"
        filename = f"DetalleContadores_{detalle.cliente}_{nro_proceso}_{sufijo}.xlsx"
        return ReporteXlsxDetalleProceso(filename=filename, contenido=contenido)


def _filtrar(
    filas: list[DetalleContadorRow], alcance: AlcanceReporte
) -> list[DetalleContadorRow]:
    if alcance == "todos":
        return filas
    return [f for f in filas if f.falta_contador]
