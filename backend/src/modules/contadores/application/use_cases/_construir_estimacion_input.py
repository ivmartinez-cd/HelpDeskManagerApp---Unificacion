from typing import Any

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.equipo_proceso_dto import (
    ClaseProceso,
    EquipoProceso,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import (
    EstimacionInput,
)


def construir_estimacion_input(
    equipo: EquipoProceso, clase: ClaseProceso, ctx: ContextoProcesoDto
) -> EstimacionInput:
    return EstimacionInput(**_campos_equipo(equipo, clase), **_campos_proceso(ctx))


def _campos_equipo(equipo: EquipoProceso, clase: ClaseProceso) -> dict[str, Any]:
    return dict(
        pendiente_estimar=not clase.ya_real,
        estado_maquina=equipo.estado_maquina,
        tecnologia=clase.tecnologia,
        velocidad_ppm=clase.velocidad_ppm,
        ultimo_contador_facturado=clase.ultimo_contador_facturado,
        ultimo_real=clase.ultimo_real,
        fecha_ultimo_real_no_t4=clase.fecha_ultimo_real_no_t4,
        real_anterior=clase.real_anterior,
        t4_mas_reciente=clase.t4_mas_reciente,
        t4_revisado=clase.t4_revisado,
        parque_cliente_modelo=clase.parque_cliente_modelo,
        parque_grupo_modelo=clase.parque_grupo_modelo,
        parque_cliente_tecnologia=clase.parque_cliente_tecnologia,
        parque_global_modelo=clase.parque_global_modelo,
        prom_6_facturados=clase.prom_6_facturados,
    )


def _campos_proceso(ctx: ContextoProcesoDto) -> dict[str, Any]:
    return dict(
        fecha_objetivo=ctx.fecha_objetivo,
        periodo_desde=ctx.periodo_desde,
        periodo_hasta=ctx.periodo_hasta,
        id_grupo_economico=ctx.id_grupo_economico,
        id_anexo=ctx.id_anexo,
        recesos=ctx.recesos,
    )
