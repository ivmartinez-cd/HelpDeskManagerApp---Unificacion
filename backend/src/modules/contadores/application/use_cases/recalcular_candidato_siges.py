from src.modules.contadores.application.dtos.recalcular_candidato_request import (
    RecalcularCandidatoRequest,
)
from src.modules.contadores.application.dtos.solicitud_recalculo_siges_dto import (
    SolicitudRecalculoSigesDto,
)
from src.modules.contadores.application.use_cases._construir_entrada_siges import (
    ConstructorEntradaSiges,
)
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.ports.recesos_port import RecesosPort
from src.modules.contadores.domain.services.estimacion.recalcular_manual import recalcular_con_pl
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef


class RecalcularCandidatoSigesUseCase:
    """Variante real de `RecalcularCandidatoUseCase`: reusa la grilla ya
    calculada para el proceso (cacheada en `PyodbcGrillaEstimacionGateway`,
    TTL 10 min) en vez de volver a correr el pipeline completo por cada P/L
    manual que prueba el operador — `None` si el equipo/clase no aparece en
    esa grilla (proceso o equipo distintos a los ya cargados)."""

    def __init__(self, gateway: GrillaEstimacionPort, recesos_store: RecesosPort) -> None:
        self._constructor = ConstructorEntradaSiges(gateway, recesos_store)

    async def execute(
        self, request: RecalcularCandidatoRequest, solicitud: SolicitudRecalculoSigesDto
    ) -> EstimacionResultado | None:
        resultado = await self._constructor.construir(request.id_maquina, request.clase, solicitud)
        if resultado is None:
            return None
        entrada, recesos = resultado
        partida = LecturaRef(
            request.partida_valor, request.partida_fecha, request.partida_tipo_toma
        )
        llegada = LecturaRef(
            request.llegada_valor, request.llegada_fecha, request.llegada_tipo_toma
        )
        return recalcular_con_pl(ContextoEstimacion(entrada, recesos), partida, llegada)
