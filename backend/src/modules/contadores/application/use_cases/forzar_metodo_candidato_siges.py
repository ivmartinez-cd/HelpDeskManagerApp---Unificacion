from src.modules.contadores.application.dtos.forzar_metodo_request import ForzarMetodoRequest
from src.modules.contadores.application.dtos.solicitud_recalculo_siges_dto import (
    SolicitudRecalculoSigesDto,
)
from src.modules.contadores.application.use_cases._construir_entrada_siges import (
    ConstructorEntradaSiges,
)
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.services.estimacion.forzar_metodo import (
    forzar_cascada_parque,
    forzar_entre_reales,
)
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.infrastructure.ejemplo.recesos_store import RecesosEjemploStore


class ForzarMetodoCandidatoSigesUseCase:
    """Variante real de `ForzarMetodoCandidatoUseCase`: mismo criterio de
    reuso de la grilla cacheada que `RecalcularCandidatoSigesUseCase`."""

    def __init__(self, gateway: GrillaEstimacionPort, recesos_store: RecesosEjemploStore) -> None:
        self._constructor = ConstructorEntradaSiges(gateway, recesos_store)

    async def execute(
        self, request: ForzarMetodoRequest, solicitud: SolicitudRecalculoSigesDto
    ) -> EstimacionResultado | None:
        resultado = await self._constructor.construir(request.id_maquina, request.clase, solicitud)
        if resultado is None:
            return None
        entrada, recesos = resultado
        ctx = ContextoEstimacion(entrada, recesos)
        if request.metodo == "entre_reales":
            return forzar_entre_reales(ctx)
        return forzar_cascada_parque(ctx)
