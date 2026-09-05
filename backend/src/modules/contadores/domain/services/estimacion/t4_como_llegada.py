from dataclasses import dataclass, replace

from src.modules.contadores.domain.services.estimacion.armado_resultado import con_marcadores
from src.modules.contadores.domain.services.estimacion.marcadores import (
    SenalesRama,
    evaluar_marcadores,
)
from src.modules.contadores.domain.services.estimacion.regla_de_tres import calcular_regla_de_tres
from src.modules.contadores.domain.services.estimacion.validez_t4 import par_valido, t4_es_valido
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

_NOTA_SIN_PARTIDA = (
    "Sin lectura previa a menos de 15 días del informe de Servicio Técnico. "
    "El operador debe elegir: marcar el T4 como facturable y reprocesar, "
    "aceptar este valor tal cual, o estimar de otra forma eligiendo "
    "Partida/Llegada a mano."
)

_BASE = EstimacionResultado(
    estim_propuesto=0,
    impresiones=0,
    tipo_toma=14,
    fuente="T4_ST",
    metodo_detalle="",
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


@dataclass(frozen=True, slots=True)
class _Propuesta:
    estimado: float
    impresiones: float
    dias_par: int | None
    dias_proyectados: int | None
    dias_receso: int
    tasa_diaria: float | None
    metodo: str
    nota_operador: str | None
    sin_partida: bool

    @property
    def otro_motivo(self) -> bool:
        return self.dias_receso > 0 or self.sin_partida


def _partida_para_t4(entrada: EstimacionInput, t4: LecturaRef) -> LecturaRef | None:
    """Se prefiere el último real sobre el último facturado como Partida
    (REGLAS_DE_NEGOCIO §5.3, CASOS_DE_PRUEBA §6 Caso D)."""
    for candidato in (entrada.ultimo_real, entrada.ultimo_contador_facturado):
        if candidato is not None and par_valido(candidato, t4):
            return candidato
    return None


def _proponer(ctx: ContextoEstimacion, t4: LecturaRef, partida: LecturaRef | None) -> _Propuesta:
    if partida is None:
        impresiones = t4.valor - ctx.entrada.ultimo_contador_facturado.valor
        return _Propuesta(
            t4.valor, impresiones, None, None, 0, None, "T4ST valor", _NOTA_SIN_PARTIDA, True
        )
    r3 = calcular_regla_de_tres(partida, t4, ctx)
    return _Propuesta(
        r3.estimado,
        r3.impresiones,
        r3.dias_par,
        r3.dias_proyectados,
        r3.dias_receso_descontados,
        r3.tasa_diaria,
        "T4ST proyectado",
        None,
        False,
    )


def intentar_t4_como_llegada(
    ctx: ContextoEstimacion, en_alerta: bool
) -> EstimacionResultado | None:
    t4 = ctx.entrada.t4_mas_reciente
    if not t4_es_valido(t4, ctx.entrada.fecha_ultimo_real_no_t4, ctx.entrada.fecha_objetivo):
        return None
    assert t4 is not None
    partida = _partida_para_t4(ctx.entrada, t4)
    propuesta = _proponer(ctx, t4, partida)
    return _armar(ctx.entrada, propuesta, en_alerta)


def _armar(entrada: EstimacionInput, propuesta: _Propuesta, en_alerta: bool) -> EstimacionResultado:
    resultado = _borrador(entrada, propuesta, en_alerta)
    senales = SenalesRama(
        t4_sin_revisar=not entrada.t4_revisado,
        requiere_confirmacion_otro_motivo=propuesta.otro_motivo,
    )
    marcadores = evaluar_marcadores(entrada, propuesta.impresiones, senales)
    return con_marcadores(resultado, marcadores)


def _borrador(
    entrada: EstimacionInput, propuesta: _Propuesta, en_alerta: bool
) -> EstimacionResultado:
    return replace(
        _BASE,
        estim_propuesto=propuesta.estimado,
        impresiones=propuesta.impresiones,
        metodo_detalle=propuesta.metodo,
        requiere_confirmacion=(not entrada.t4_revisado) or propuesta.otro_motivo,
        nota_operador=propuesta.nota_operador,
        meses_sin_real_en_alerta=en_alerta,
        dias_par_pl=propuesta.dias_par,
        ajustado_por_receso=propuesta.dias_receso > 0,
        dias_receso_descontados=propuesta.dias_receso,
        dias_proyectados=propuesta.dias_proyectados,
        t4_sin_revisar=not entrada.t4_revisado,
        tasa_diaria=propuesta.tasa_diaria,
    )
