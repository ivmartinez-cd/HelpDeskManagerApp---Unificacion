"""`EstimarConT4ST` del legacy: el T4 ST entra como LLEGADA de una regla de
tres y se proyecta a la fecha objetivo. Partida: último real; si no sirve,
último contador facturado (misma regla que un par P/L: 15 días y P <= L).
Sin Partida válida — o en un Backup, que no se proyecta — se propone el valor
del T4 tal cual. El tipo de toma sugerido es SIEMPRE 14."""

from src.modules.contadores.domain.services.estimacion.detalle_t4 import (
    Partida,
    detalle_t4_proyectado,
    detalle_t4_tal_cual,
    etiqueta_t4_proyectado,
)
from src.modules.contadores.domain.services.estimacion.marcas_estimacion import marcas
from src.modules.contadores.domain.services.estimacion.redondeo import (
    a_decimal,
    a_float,
    contador_anterior_o_cero,
    redondear,
)
from src.modules.contadores.domain.services.estimacion.regla_de_tres import (
    calcular_regla_de_tres,
    campos_regla_de_tres,
)
from src.modules.contadores.domain.services.estimacion.validez_t4 import (
    DIAS_MINIMOS_SEPARACION_PL,
    t4_llegada_valida,
)
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

_TIPO_TOMA_ESTIMADO = 14
NOTA_SIN_PAR = (
    "Decidir: 1) marcar el T4 facturable en SiGes y reprocesar · "
    "2) aceptar este valor (se graba T14) · "
    "3) estimar de otra forma desde el panel de candidatos"
)


def t4_aplicable(entrada: EstimacionInput) -> bool:
    """Hay T4 ST y todavía vale como Llegada (`T4LlegadaValida`)."""
    t4 = entrada.t4_mas_reciente
    if t4 is None:
        return False
    return t4_llegada_valida(t4.fecha, entrada.fecha_ultimo_real_no_t4, entrada.fecha_objetivo)


def estimar_con_t4(ctx: ContextoEstimacion, proyectar: bool = True) -> EstimacionResultado | None:
    """Sin marcadores (los aplica quien lo llama). `proyectar=False` es el
    caso Backup: valor tal cual, sin nota para el operador."""
    t4 = ctx.entrada.t4_mas_reciente
    if t4 is None:
        return None
    partida = _partida(ctx.entrada, t4) if proyectar else None
    if partida is not None:
        return _proyectado(ctx, t4, partida)
    return _tal_cual(ctx.entrada, t4, sin_par=proyectar)


def _partida(entrada: EstimacionInput, t4: LecturaRef) -> Partida | None:
    """`EsPartidaValida` del legacy, probando último real y después último
    facturado."""
    for lectura, descripcion in (
        (entrada.ultimo_real, "últ. real"),
        (entrada.ultimo_contador_facturado, "últ. facturado"),
    ):
        if lectura is not None and _es_partida_valida(lectura, t4):
            return Partida(lectura, descripcion)
    return None


def _es_partida_valida(lectura: LecturaRef, t4: LecturaRef) -> bool:
    dias = (t4.fecha - lectura.fecha).days
    return dias >= DIAS_MINIMOS_SEPARACION_PL and lectura.valor <= t4.valor


def _proyectado(ctx: ContextoEstimacion, t4: LecturaRef, partida: Partida) -> EstimacionResultado:
    revisado = ctx.entrada.t4_revisado
    r3 = calcular_regla_de_tres(partida.lectura, t4, ctx)
    return EstimacionResultado(
        tipo_toma=_TIPO_TOMA_ESTIMADO,
        fuente="T4_ST",
        metodo_detalle="T4ST proyectado",
        metodo="T4ST_Proyectado",
        requiere_confirmacion=not revisado or r3.ajustado_por_receso,
        t4_sin_revisar=not revisado,
        detalle_calculo=detalle_t4_proyectado(partida, t4, r3, revisado),
        etiqueta_nivel=etiqueta_t4_proyectado(partida, revisado),
        marcas=marcas(
            ("T4SinRevisar", not revisado), ("AjustadoPorReceso", r3.ajustado_por_receso)
        ),
        **campos_regla_de_tres(r3),
    )


def _tal_cual(entrada: EstimacionInput, t4: LecturaRef, sin_par: bool) -> EstimacionResultado:
    revisado = entrada.t4_revisado
    valor = a_decimal(t4.valor)
    texto = detalle_t4_tal_cual(revisado, sin_par)
    return EstimacionResultado(
        estim_propuesto=a_float(redondear(valor)),
        impresiones=a_float(redondear(valor - contador_anterior_o_cero(entrada))),
        tipo_toma=_TIPO_TOMA_ESTIMADO,
        fuente="T4_ST",
        metodo_detalle="T4ST valor",
        metodo="T4ST_Valor",
        requiere_confirmacion=not revisado or sin_par,
        t4_sin_revisar=not revisado,
        nota_operador=NOTA_SIN_PAR if sin_par else None,
        detalle_calculo=texto,
        etiqueta_nivel=texto,
        marcas=marcas(("T4SinRevisar", not revisado), ("SinParValido", sin_par)),
    )
