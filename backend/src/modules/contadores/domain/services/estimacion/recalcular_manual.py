from dataclasses import replace

from src.modules.contadores.domain.services.estimacion.detalle_calculo import (
    detalle_pl,
    etiqueta_pl,
)
from src.modules.contadores.domain.services.estimacion.marcadores import finalizar
from src.modules.contadores.domain.services.estimacion.marcas_estimacion import marcas
from src.modules.contadores.domain.services.estimacion.regla_de_tres import (
    ReglaDeTres,
    calcular_regla_de_tres,
    campos_regla_de_tres,
)
from src.modules.contadores.domain.services.estimacion.validez_t4 import par_valido
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    MarcaEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

_TIPO_TOMA_ST = 4
_TIPO_TOMA_ESTIMADO = 14


def recalcular_con_pl(
    ctx: ContextoEstimacion,
    partida: LecturaRef,
    llegada: LecturaRef,
    alerta_vigente: bool = False,
) -> EstimacionResultado | None:
    """`RecalcularConPL` del legacy (regla de tres sobre la pareja elegida a
    mano; tipo de toma SIEMPRE 14). `None` = pareja inválida: quien llama
    conserva la fila vigente. Como el legacy (`actual with {...}`), una fila
    ya real hereda la alerta de meses de la fila efectiva: `alerta_vigente`
    (False sin override; la del método forzado si lo hubo). En una pendiente
    toda rama del legacy la calcula igual, así que se recalcula."""
    if not par_valido(partida, llegada):
        return None
    r3 = calcular_regla_de_tres(partida, llegada, ctx)
    final = finalizar(_borrador(partida, llegada, r3), ctx.entrada)
    if ctx.entrada.pendiente_estimar:
        return final
    return replace(final, meses_sin_real_en_alerta=alerta_vigente)


def _borrador(partida: LecturaRef, llegada: LecturaRef, r3: ReglaDeTres) -> EstimacionResultado:
    es_t4 = llegada.tipo_toma == _TIPO_TOMA_ST
    sin_revisar = es_t4 and not llegada.para_facturar
    return EstimacionResultado(
        tipo_toma=_TIPO_TOMA_ESTIMADO,
        fuente="T4_ST" if es_t4 else "Historia_Propia",
        metodo_detalle="Partida/Llegada elegidas a mano",
        metodo="T4ST_Valor" if es_t4 else "EntreReales",
        requiere_confirmacion=es_t4 or r3.ajustado_por_receso,
        par_incluye_t4=es_t4,
        t4_sin_revisar=sin_revisar,
        detalle_calculo=detalle_pl(partida, llegada, r3),
        etiqueta_nivel=etiqueta_pl(partida, llegada, r3),
        marcas=_marcas_pl(es_t4, sin_revisar, r3),
        **campos_regla_de_tres(r3),
    )


def _marcas_pl(es_t4: bool, sin_revisar: bool, r3: ReglaDeTres) -> frozenset[MarcaEstimacion]:
    return marcas(
        ("PLManual", True),
        ("UsaT4EnPar", es_t4),
        ("AjustadoPorReceso", r3.ajustado_por_receso),
        ("InterpoladoAtras", r3.dias_proyectados < 0),
        ("T4SinRevisar", sin_revisar),
    )
