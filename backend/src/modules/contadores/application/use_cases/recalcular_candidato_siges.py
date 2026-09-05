from dataclasses import dataclass
from datetime import date

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto
from src.modules.contadores.application.dtos.recalcular_candidato_request import (
    RecalcularCandidatoRequest,
)
from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.application.use_cases._mapear_filas_grilla_siges import (
    agrupar_por_equipo,
)
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.services.estimacion.recalcular_manual import recalcular_con_pl
from src.modules.contadores.domain.services.estimacion.recesos import recesos_aplicables
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef
from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente
from src.modules.contadores.infrastructure.ejemplo.recesos_store import RecesosEjemploStore


@dataclass(frozen=True, slots=True)
class SolicitudRecalculoSigesDto:
    """Lo que el frontend ya tiene tras elegir Grupo económico → Proceso —
    identifica qué grilla cacheada reusar (agrupado, ARCHITECTURE_GUIDE.md
    §4)."""

    nro_proceso: int
    id_grupo_economico: int
    id_anexo: int
    fecha_objetivo: date


class RecalcularCandidatoSigesUseCase:
    """Variante real de `RecalcularCandidatoUseCase`: reusa la grilla ya
    calculada para el proceso (cacheada en `PyodbcGrillaEstimacionGateway`,
    TTL 10 min) en vez de volver a correr el pipeline completo por cada P/L
    manual que prueba el operador — `None` si el equipo/clase no aparece en
    esa grilla (proceso o equipo distintos a los ya cargados)."""

    def __init__(self, gateway: GrillaEstimacionPort, recesos_store: RecesosEjemploStore) -> None:
        self._gateway = gateway
        self._recesos_store = recesos_store

    async def execute(
        self, request: RecalcularCandidatoRequest, solicitud: SolicitudRecalculoSigesDto
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
        partida = LecturaRef(
            request.partida_valor, request.partida_fecha, request.partida_tipo_toma
        )
        llegada = LecturaRef(
            request.llegada_valor, request.llegada_fecha, request.llegada_tipo_toma
        )
        return recalcular_con_pl(ContextoEstimacion(entrada, recesos), partida, llegada)

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
