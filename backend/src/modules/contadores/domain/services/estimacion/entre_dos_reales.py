from src.modules.contadores.domain.services.estimacion.detalle_calculo import (
    detalle_entre_reales,
    etiqueta_entre_reales,
)
from src.modules.contadores.domain.services.estimacion.marcas_estimacion import marcas
from src.modules.contadores.domain.services.estimacion.regla_de_tres import (
    ReglaDeTres,
    calcular_regla_de_tres,
    campos_regla_de_tres,
)
from src.modules.contadores.domain.services.estimacion.validez_t4 import (
    par_entre_reales_valido,
    t4_llegada_valida,
)
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    MarcaEstimacion,
)

_TIPO_TOMA_ST = 4
_TIPO_TOMA_ESTIMADO = 14


def hay_par_entre_reales(entrada: EstimacionInput) -> bool:
    """`PuedeCalcularEntreReales` del legacy."""
    if entrada.ultimo_real is None or entrada.real_anterior is None:
        return False
    return par_entre_reales_valido(entrada.real_anterior, entrada.ultimo_real)


def estimar_entre_reales(ctx: ContextoEstimacion) -> EstimacionResultado:
    """`EstimarEntreReales` del legacy, sin marcadores (los aplica quien lo
    llama). Requiere `hay_par_entre_reales`. Llegada posterior a la fecha
    objetivo interpola hacia atrás (solo avisado; el valor sale igual)."""
    entrada = ctx.entrada
    assert entrada.ultimo_real is not None and entrada.real_anterior is not None
    r3 = calcular_regla_de_tres(entrada.real_anterior, entrada.ultimo_real, ctx)
    incluye_t4 = _par_incluye_t4(entrada)
    return EstimacionResultado(
        tipo_toma=_TIPO_TOMA_ESTIMADO,
        fuente="Historia_Propia",
        metodo_detalle="Entre dos reales",
        metodo="EntreReales",
        requiere_confirmacion=incluye_t4 or r3.ajustado_por_receso,
        par_incluye_t4=incluye_t4,
        detalle_calculo=detalle_entre_reales(r3, incluye_t4),
        etiqueta_nivel=etiqueta_entre_reales(r3, incluye_t4),
        marcas=_marcas(r3, incluye_t4),
        **campos_regla_de_tres(r3),
    )


def _marcas(r3: ReglaDeTres, incluye_t4: bool) -> frozenset[MarcaEstimacion]:
    return marcas(
        ("AjustadoPorReceso", r3.ajustado_por_receso),
        ("UsaT4EnPar", incluye_t4),
        ("InterpoladoAtras", r3.dias_proyectados < 0),
    )


def conserva_negativo(entrada: EstimacionInput) -> bool:
    """Un resultado negativo entre reales se conserva solo si el último real
    es un T4 que todavía vale como Llegada (T4 corrector); si no, la fila cae
    al T4 ST / cascada."""
    ultimo = entrada.ultimo_real
    if ultimo is None or ultimo.tipo_toma != _TIPO_TOMA_ST:
        return False
    return t4_llegada_valida(ultimo.fecha, entrada.fecha_ultimo_real_no_t4, entrada.fecha_objetivo)


def _par_incluye_t4(entrada: EstimacionInput) -> bool:
    assert entrada.ultimo_real is not None and entrada.real_anterior is not None
    return _TIPO_TOMA_ST in (entrada.ultimo_real.tipo_toma, entrada.real_anterior.tipo_toma)
