from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto
from src.modules.contadores.application.dtos.forzar_metodo_request import ForzarMetodoRequest
from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.application.use_cases._mapear_filas_grilla_siges import (
    agrupar_por_equipo,
)
from src.modules.contadores.application.use_cases.recalcular_candidato_siges import (
    SolicitudRecalculoSigesDto,
)
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.services.estimacion.forzar_metodo import (
    forzar_cascada_parque,
    forzar_entre_reales,
)
from src.modules.contadores.domain.services.estimacion.recesos import recesos_aplicables
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente
from src.modules.contadores.infrastructure.ejemplo.recesos_store import RecesosEjemploStore


class ForzarMetodoCandidatoSigesUseCase:
    """Variante real de `ForzarMetodoCandidatoUseCase`: mismo criterio de
    reuso de la grilla cacheada que `RecalcularCandidatoSigesUseCase`."""

    def __init__(self, gateway: GrillaEstimacionPort, recesos_store: RecesosEjemploStore) -> None:
        self._gateway = gateway
        self._recesos_store = recesos_store

    async def execute(
        self, request: ForzarMetodoRequest, solicitud: SolicitudRecalculoSigesDto
    ) -> EstimacionResultado | None:
        filas = await self._gateway.fetch_grilla(solicitud.nro_proceso, solicitud.fecha_objetivo)
        filas_equipo = [
            f
            for f in filas
            if f.id_maquina == request.id_maquina and str(f.id_clase_contador) == request.clase
        ]
        if not filas_equipo:
            return None
        equipo = agrupar_por_equipo(filas_equipo)[0]
        ctx = self._contexto(filas_equipo[0], solicitud)
        entrada = construir_estimacion_input(equipo, equipo.clases[0], ctx)
        recesos = recesos_aplicables(ctx.recesos, ctx.id_anexo, ctx.id_grupo_economico)
        ctx_estimacion = ContextoEstimacion(entrada, recesos)
        if request.metodo == "entre_reales":
            return forzar_entre_reales(ctx_estimacion)
        return forzar_cascada_parque(ctx_estimacion)

    def _contexto(
        self, fila: FilaGrillaSigesDto, solicitud: SolicitudRecalculoSigesDto
    ) -> ContextoProcesoDto:
        recesos = self._recesos_store.listar(solicitud.id_grupo_economico)
        return ContextoProcesoDto(
            fecha_objetivo=solicitud.fecha_objetivo,
            periodo_desde=fila.periodo_desde,
            periodo_hasta=fila.periodo_hasta,
            id_grupo_economico=solicitud.id_grupo_economico,
            id_anexo=solicitud.id_anexo,
            recesos=[_a_receso_cliente(r) for r in recesos],
        )


def _a_receso_cliente(r: RecesoDto) -> RecesoCliente:
    return RecesoCliente(r.fecha_desde, r.fecha_hasta, r.id_grupo_economico, r.id_anexo)
