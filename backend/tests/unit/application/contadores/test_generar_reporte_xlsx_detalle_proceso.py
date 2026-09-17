"""GenerarReporteXlsxDetalleProcesoUseCase con un puerto y un writer fake:
verifica el filtro por `alcance` (todos vs. solo falta contador) y que el
nombre de archivo sale del cliente/proceso, no de un input del formulario."""

from src.modules.contadores.application.use_cases.generar_reporte_xlsx_detalle_proceso import (
    GenerarReporteXlsxDetalleProcesoUseCase,
)
from src.modules.contadores.domain.ports.detalle_contador_proceso_port import (
    DetalleContadorProceso,
)
from src.modules.contadores.domain.value_objects.detalle_contador_row import (
    DetalleContadorRow,
)


class FakePort:
    def __init__(self, proceso: DetalleContadorProceso) -> None:
        self._proceso = proceso

    async def fetch(self, nro_proceso: int) -> DetalleContadorProceso:
        return self._proceso


class FakeWriter:
    def __init__(self) -> None:
        self.filas_recibidas: list[DetalleContadorRow] | None = None
        self.cliente_recibido: str | None = None
        self.nro_proceso_recibido: int | None = None

    def write(self, filas: list[DetalleContadorRow], cliente: str, nro_proceso: int) -> bytes:
        self.filas_recibidas = filas
        self.cliente_recibido = cliente
        self.nro_proceso_recibido = nro_proceso
        return b"xlsx-bytes"


def _fila(serie: str, falta_contador: bool) -> DetalleContadorRow:
    return DetalleContadorRow(
        empresa="ISSN",
        sucursal="Botiquin Caviahue",
        sector="Indeterminado",
        modelo="MFP Mono HP 432fdn",
        serie=serie,
        nombre_clase="Mono",
        fecha_toma_anterior=None,
        contador_anterior=1,
        fecha_toma_actual=None,
        contador_actual=0 if falta_contador else 40,
        impresiones_reales=0.0,
        estado_maquina="Activa en Cliente",
        direccion_ip=None,
        mascara_ip=None,
        falta_contador=falta_contador,
        tipo="FALTA CONTADOR Mono" if falta_contador else None,
        nro_proceso=99089,
        nombre_anexo="Anexo Principal",
        periodo_facturacion="2026-08",
    )


async def test_alcance_todos_incluye_todas_las_filas() -> None:
    proceso = DetalleContadorProceso(
        cliente="ISSN", filas=[_fila("A", True), _fila("B", False)]
    )
    writer = FakeWriter()
    use_case = GenerarReporteXlsxDetalleProcesoUseCase(FakePort(proceso), writer)  # type: ignore[arg-type]

    resultado = await use_case.execute(99089, "todos")

    assert writer.filas_recibidas == proceso.filas
    assert writer.cliente_recibido == "ISSN"
    assert writer.nro_proceso_recibido == 99089
    assert resultado.filename == "DetalleContadores_ISSN_99089_Completo.xlsx"
    assert resultado.contenido == b"xlsx-bytes"


async def test_alcance_falta_contador_filtra_las_filas() -> None:
    fila_falta = _fila("A", True)
    fila_ok = _fila("B", False)
    proceso = DetalleContadorProceso(cliente="ISSN", filas=[fila_falta, fila_ok])
    writer = FakeWriter()
    use_case = GenerarReporteXlsxDetalleProcesoUseCase(FakePort(proceso), writer)  # type: ignore[arg-type]

    resultado = await use_case.execute(99089, "falta_contador")

    assert writer.filas_recibidas == [fila_falta]
    assert resultado.filename == "DetalleContadores_ISSN_99089_FaltaContador.xlsx"
