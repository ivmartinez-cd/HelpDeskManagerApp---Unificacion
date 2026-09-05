from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.recalcular_candidato_request import (
    RecalcularCandidatoRequest,
)
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.application.use_cases.get_candidatos_equipo import buscar_equipo_y_clase
from src.modules.contadores.domain.services.estimacion.recalcular_manual import recalcular_con_pl
from src.modules.contadores.domain.services.estimacion.recesos import recesos_aplicables
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef


class RecalcularCandidatoUseCase:
    def execute(
        self, request: RecalcularCandidatoRequest, ctx: ContextoProcesoDto
    ) -> EstimacionResultado | None:
        equipo, clase = buscar_equipo_y_clase(request.id_maquina, request.clase)
        if equipo is None or clase is None:
            return None
        entrada = construir_estimacion_input(equipo, clase, ctx)
        recesos = recesos_aplicables(ctx.recesos, ctx.id_anexo, ctx.id_grupo_economico)
        partida = LecturaRef(
            request.partida_valor, request.partida_fecha, request.partida_tipo_toma
        )
        llegada = LecturaRef(
            request.llegada_valor, request.llegada_fecha, request.llegada_tipo_toma
        )
        return recalcular_con_pl(ContextoEstimacion(entrada, recesos), partida, llegada)
