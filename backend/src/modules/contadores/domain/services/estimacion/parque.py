from dataclasses import dataclass
from decimal import Decimal

from src.modules.contadores.domain.services.estimacion.antiguedad import meses_entre
from src.modules.contadores.domain.services.estimacion.aritmetica_decimal_cs import (
    dividir,
    multiplicar,
)
from src.modules.contadores.domain.services.estimacion.cascada_parque import (
    NivelParque,
    resolver_cascada_parque,
)
from src.modules.contadores.domain.services.estimacion.formato_es_ar import dos_decimales, entero
from src.modules.contadores.domain.services.estimacion.marcas_estimacion import marcas
from src.modules.contadores.domain.services.estimacion.recesos import dias_activos
from src.modules.contadores.domain.services.estimacion.redondeo import (
    a_float,
    base_cascada,
    redondear,
)
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    DetalleParque,
    EstimacionResultado,
)

_TIPO_TOMA_PROMEDIO = 19


@dataclass(frozen=True, slots=True)
class _Calculo:
    nivel: NivelParque
    factor: Decimal
    dias_descontados: int
    impresiones: Decimal

    @property
    def ajustado(self) -> bool:
        return self.factor < 1


def estimar_cascada_t19(ctx: ContextoEstimacion) -> EstimacionResultado | None:
    """`EstimarCascadaT19` del legacy, sin marcadores: impresiones =
    Round(Round(promedio) × fracción de días activos del período) sumadas al
    contador anterior (o al último real, o a 0). Siempre T19 y a confirmar."""
    nivel = resolver_cascada_parque(ctx.entrada)
    if nivel is None:
        return None
    return _resultado(_calcular(nivel, ctx), ctx.entrada)


def _resultado(calculo: _Calculo, entrada: EstimacionInput) -> EstimacionResultado:
    nivel = calculo.nivel
    return EstimacionResultado(
        estim_propuesto=a_float(redondear(base_cascada(entrada) + calculo.impresiones)),
        impresiones=a_float(calculo.impresiones),
        tipo_toma=_TIPO_TOMA_PROMEDIO,
        fuente=nivel.fuente,
        metodo_detalle=f"Cascada de parque: {nivel.fuente}",
        metodo="MedianaTruncadaP80" if nivel.es_mediana_truncada else "MedianaCruda",
        marcas=marcas(("AjustadoPorReceso", calculo.ajustado)),
        requiere_confirmacion=True,
        ajustado_por_receso=calculo.ajustado,
        dias_receso_descontados=calculo.dias_descontados,
        detalle_parque=_detalle_parque(nivel),
        detalle_calculo=_detalle(calculo, entrada),
        etiqueta_nivel=nivel.etiqueta + (" · ajustado por receso" if calculo.ajustado else ""),
    )


def _calcular(nivel: NivelParque, ctx: ContextoEstimacion) -> _Calculo:
    """`FactorActivoPeriodo` del legacy: días activos / días del período del
    proceso; 1 si no hay recesos aplicables o el período no tiene días."""
    entrada = ctx.entrada
    dias = (entrada.periodo_hasta - entrada.periodo_desde).days
    if dias <= 0 or not ctx.recesos:
        return _Calculo(nivel, Decimal(1), 0, nivel.impresiones)
    activos = dias_activos(entrada.periodo_desde, entrada.periodo_hasta, ctx.recesos)
    factor = dividir(Decimal(activos), dias)
    impresiones = redondear(multiplicar(nivel.impresiones, factor))
    return _Calculo(nivel, factor, dias - activos, impresiones)


def _detalle(calculo: _Calculo, entrada: EstimacionInput) -> str:
    nivel = calculo.nivel
    receso = ""
    if calculo.ajustado:
        receso = f" · receso ×{dos_decimales(calculo.factor)} (de {entero(nivel.impresiones)} imp)"
    return (
        f"{_origen(entrada)} · {nivel.etiqueta} · {nivel.etiqueta_metodo} · "
        f"+{entero(calculo.impresiones)} imp{receso}"
    )


def _origen(entrada: EstimacionInput) -> str:
    if entrada.ultimo_real is None:
        return "Sin historia propia"
    meses = meses_entre(entrada.ultimo_real.fecha, entrada.fecha_objetivo)
    return f"Historia propia vieja ({meses}m sin real)"


def _detalle_parque(nivel: NivelParque) -> DetalleParque:
    return DetalleParque(
        n_equipos=nivel.promedio.n_equipos,
        n_descartados=nivel.promedio.n_descartados,
        es_mediana_truncada=nivel.es_mediana_truncada,
        mediana_cruda=nivel.promedio.mediana_cruda,
        media_cruda=nivel.promedio.media_cruda,
    )
