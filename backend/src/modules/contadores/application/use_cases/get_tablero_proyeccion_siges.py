"""Tablero de Proyección con datos reales de Siges — mismo pipeline que el
modo ejemplo (`get_tablero_proyeccion.py`), reemplazando la fuente de
equipos por la consulta real (MODELO_DE_DATOS.md §3.4)."""

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto
from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.dtos.resumen_proyeccion_dto import ResumenProyeccionDto
from src.modules.contadores.application.dtos.solicitud_tablero_siges_dto import (
    SolicitudTableroSigesDto,
)
from src.modules.contadores.application.use_cases._mapear_filas_grilla_siges import (
    agrupar_por_equipo,
)
from src.modules.contadores.application.use_cases.get_tablero_proyeccion import (
    GetTableroProyeccionUseCase,
    TableroProyeccionResult,
)
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente
from src.modules.contadores.infrastructure.ejemplo.decisiones_operador_store import (
    DecisionesOperadorStore,
)
from src.modules.contadores.infrastructure.ejemplo.recesos_store import RecesosEjemploStore

_RESUMEN_VACIO = ResumenProyeccionDto(reales=0, estimados=0, pendientes=0, sospechosos=0, total=0)


class GetTableroProyeccionSigesUseCase:
    def __init__(
        self,
        gateway: GrillaEstimacionPort,
        decisiones: DecisionesOperadorStore,
        recesos_store: RecesosEjemploStore,
    ) -> None:
        self._gateway = gateway
        self._decisiones = decisiones
        self._recesos_store = recesos_store

    async def execute(self, solicitud: SolicitudTableroSigesDto) -> TableroProyeccionResult:
        filas_siges = await self._gateway.fetch_grilla(
            solicitud.nro_proceso, solicitud.fecha_objetivo
        )
        if not filas_siges:
            return TableroProyeccionResult([], _RESUMEN_VACIO)
        equipos = agrupar_por_equipo(filas_siges)
        ctx = self._contexto(filas_siges[0], solicitud)
        return GetTableroProyeccionUseCase(self._decisiones, lambda: equipos).execute(ctx)

    def _contexto(
        self, primera: FilaGrillaSigesDto, solicitud: SolicitudTableroSigesDto
    ) -> ContextoProcesoDto:
        recesos = self._recesos_store.listar(solicitud.id_grupo_economico)
        return ContextoProcesoDto(
            fecha_objetivo=solicitud.fecha_objetivo,
            periodo_desde=primera.periodo_desde,
            periodo_hasta=primera.periodo_hasta,
            id_grupo_economico=solicitud.id_grupo_economico,
            id_anexo=solicitud.id_anexo,
            recesos=[_a_receso_cliente(r) for r in recesos],
        )


def _a_receso_cliente(r: RecesoDto) -> RecesoCliente:
    return RecesoCliente(r.fecha_desde, r.fecha_hasta, r.id_grupo_economico, r.id_anexo)
