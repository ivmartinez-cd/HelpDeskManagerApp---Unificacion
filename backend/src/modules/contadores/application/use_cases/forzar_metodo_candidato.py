from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.forzar_metodo_request import ForzarMetodoRequest
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.application.use_cases.get_candidatos_equipo import buscar_equipo_y_clase
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


class ForzarMetodoCandidatoUseCase:
    def execute(
        self, request: ForzarMetodoRequest, ctx: ContextoProcesoDto
    ) -> EstimacionResultado | None:
        equipo, clase = buscar_equipo_y_clase(request.id_maquina, request.clase)
        if equipo is None or clase is None:
            return None
        entrada = construir_estimacion_input(equipo, clase, ctx)
        recesos = recesos_aplicables(ctx.recesos, ctx.id_anexo, ctx.id_grupo_economico)
        ctx_estimacion = ContextoEstimacion(entrada, recesos)
        if request.metodo == "entre_reales":
            return forzar_entre_reales(ctx_estimacion)
        return forzar_cascada_parque(ctx_estimacion)
