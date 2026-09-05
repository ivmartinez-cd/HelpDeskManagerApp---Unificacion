from dataclasses import dataclass, replace

from src.modules.contadores.domain.services.estimacion.armado_resultado import con_marcadores
from src.modules.contadores.domain.services.estimacion.cascada_parque import resolver_cascada_parque
from src.modules.contadores.domain.services.estimacion.marcadores import (
    SenalesRama,
    evaluar_marcadores,
)
from src.modules.contadores.domain.services.estimacion.recesos import dias_activos
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)

_BASE = EstimacionResultado(
    estim_propuesto=0,
    impresiones=0,
    tipo_toma=19,
    fuente="Parque_Cliente_Modelo",
    metodo_detalle="",
    requiere_confirmacion=True,
    semaforo="ROJO",
    borde_salto_imposible=False,
    coloreo=None,
    nota_operador=None,
    meses_sin_real_en_alerta=False,
    dias_par_pl=None,
    ajustado_por_receso=False,
    dias_receso_descontados=0,
)


@dataclass(frozen=True, slots=True)
class _EscaladoPorReceso:
    factor: float
    dias_descontados: int


def _escalado_por_receso(ctx: ContextoEstimacion) -> _EscaladoPorReceso:
    """El valor de un nivel de parque representa un período típico sin
    recesos: se escala por la fracción de días activos del período del
    proceso que se está facturando (REGLAS_DE_NEGOCIO §6)."""
    entrada = ctx.entrada
    dias_total = (entrada.periodo_hasta - entrada.periodo_desde).days
    if dias_total <= 0:
        return _EscaladoPorReceso(1.0, 0)
    dias_activos_periodo = dias_activos(entrada.periodo_desde, entrada.periodo_hasta, ctx.recesos)
    dias_descontados = max(dias_total - dias_activos_periodo, 0)
    return _EscaladoPorReceso(dias_activos_periodo / dias_total, dias_descontados)


@dataclass(frozen=True, slots=True)
class _PropuestaParque:
    fuente: FuenteEstimacion
    impresiones: float
    escalado: _EscaladoPorReceso
    en_alerta: bool


def intentar_parque(ctx: ContextoEstimacion, en_alerta: bool) -> EstimacionResultado | None:
    """Fallback estadístico (REGLAS_DE_NEGOCIO §5.5), siempre T19 y siempre
    requiere confirmación."""
    nivel = resolver_cascada_parque(ctx.entrada)
    if nivel is None:
        return None
    escalado = _escalado_por_receso(ctx)
    impresiones = nivel.promedio.valor * escalado.factor
    propuesta = _PropuestaParque(nivel.fuente, impresiones, escalado, en_alerta)
    resultado = _borrador(ctx, propuesta)
    senales = SenalesRama(es_cascada_parque=True, requiere_confirmacion_otro_motivo=True)
    marcadores = evaluar_marcadores(ctx.entrada, impresiones, senales)
    return con_marcadores(resultado, marcadores)


def _borrador(ctx: ContextoEstimacion, propuesta: _PropuestaParque) -> EstimacionResultado:
    return replace(
        _BASE,
        estim_propuesto=ctx.entrada.ultimo_contador_facturado.valor + propuesta.impresiones,
        impresiones=propuesta.impresiones,
        fuente=propuesta.fuente,
        metodo_detalle=f"Cascada de parque: {propuesta.fuente}",
        meses_sin_real_en_alerta=propuesta.en_alerta,
        ajustado_por_receso=propuesta.escalado.dias_descontados > 0,
        dias_receso_descontados=propuesta.escalado.dias_descontados,
    )
