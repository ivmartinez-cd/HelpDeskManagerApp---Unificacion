from dataclasses import dataclass, replace

from src.modules.contadores.domain.services.estimacion.armado_resultado import con_marcadores
from src.modules.contadores.domain.services.estimacion.marcadores import (
    SenalesRama,
    evaluar_marcadores,
)
from src.modules.contadores.domain.services.estimacion.regla_de_tres import (
    ResultadoReglaDeTres,
    calcular_regla_de_tres,
)
from src.modules.contadores.domain.services.estimacion.validez_t4 import par_valido
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

_TIPO_TOMA_ST = 4

_BASE = EstimacionResultado(
    estim_propuesto=0,
    impresiones=0,
    tipo_toma=14,
    fuente="Historia_Propia",
    metodo_detalle="Entre dos reales",
    requiere_confirmacion=False,
    semaforo="VERDE",
    borde_salto_imposible=False,
    coloreo=None,
    nota_operador=None,
    meses_sin_real_en_alerta=False,
    dias_par_pl=None,
    ajustado_por_receso=False,
    dias_receso_descontados=0,
)


def hay_par_utilizable(entrada: EstimacionInput, en_alerta: bool) -> bool:
    if en_alerta or entrada.ultimo_real is None or entrada.real_anterior is None:
        return False
    return par_valido(entrada.real_anterior, entrada.ultimo_real)


def intentar_entre_dos_reales(ctx: ContextoEstimacion) -> EstimacionResultado | None:
    """Caso ideal: regla de tres sobre la propia historia del equipo
    (REGLAS_DE_NEGOCIO §5.2). Un resultado negativo se descarta acá — la
    excepción de conservarlo negativo es exclusiva de un T4 corrector
    (§5.3), no de este caso."""
    entrada = ctx.entrada
    assert entrada.ultimo_real is not None and entrada.real_anterior is not None
    r3 = calcular_regla_de_tres(entrada.real_anterior, entrada.ultimo_real, ctx)
    if r3.impresiones < 0:
        return None
    return _armar(ctx, r3)


def _par_incluye_t4(entrada: EstimacionInput) -> bool:
    assert entrada.ultimo_real is not None and entrada.real_anterior is not None
    return (
        entrada.real_anterior.tipo_toma == _TIPO_TOMA_ST
        or entrada.ultimo_real.tipo_toma == _TIPO_TOMA_ST
    )


@dataclass(frozen=True, slots=True)
class _Flags:
    """Llegada posterior a la fecha objetivo (interpolación hacia atrás,
    `dias_proyectados < 0`) fuerza `bloqueo_obligatorio` (REGLAS_DE_NEGOCIO
    §14, decisión 2026-09-05): no alcanza con el aviso de `requiere_confirmacion`,
    `resolver_resultado_final` no deja salir este valor sin que el operador
    lo acepte o corrija a mano."""

    otro_motivo: bool
    interpola_hacia_atras: bool

    @property
    def requiere_confirmacion(self) -> bool:
        return self.otro_motivo or self.interpola_hacia_atras


def _flags_de(ctx: ContextoEstimacion, r3: ResultadoReglaDeTres) -> _Flags:
    return _Flags(
        otro_motivo=_par_incluye_t4(ctx.entrada) or r3.dias_receso_descontados > 0,
        interpola_hacia_atras=r3.dias_proyectados < 0,
    )


def _armar(ctx: ContextoEstimacion, r3: ResultadoReglaDeTres) -> EstimacionResultado:
    flags = _flags_de(ctx, r3)
    senales = SenalesRama(requiere_confirmacion_otro_motivo=flags.requiere_confirmacion)
    marcadores = evaluar_marcadores(ctx.entrada, r3.impresiones, senales)
    resultado = replace(
        _BASE,
        estim_propuesto=r3.estimado,
        impresiones=r3.impresiones,
        requiere_confirmacion=flags.requiere_confirmacion,
        bloqueo_obligatorio=flags.interpola_hacia_atras,
        dias_par_pl=r3.dias_par,
        ajustado_por_receso=r3.dias_receso_descontados > 0,
        dias_receso_descontados=r3.dias_receso_descontados,
        dias_proyectados=r3.dias_proyectados,
        par_incluye_t4=_par_incluye_t4(ctx.entrada),
        tasa_diaria=r3.tasa_diaria,
    )
    return con_marcadores(resultado, marcadores)
