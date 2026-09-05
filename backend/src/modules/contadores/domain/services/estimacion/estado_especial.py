from dataclasses import replace

from src.modules.contadores.domain.services.estimacion.validez_t4 import t4_es_valido
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

_BASE = EstimacionResultado(
    estim_propuesto=None,
    impresiones=None,
    tipo_toma=14,
    fuente="EnTransito",
    metodo_detalle="",
    requiere_confirmacion=True,
    semaforo="AMARILLO",
    borde_salto_imposible=False,
    coloreo=None,
    nota_operador=None,
    meses_sin_real_en_alerta=False,
    dias_par_pl=None,
    ajustado_por_receso=False,
    dias_receso_descontados=0,
)


def _sin_movimiento(entrada: EstimacionInput, fuente: FuenteEstimacion) -> EstimacionResultado:
    return replace(
        _BASE,
        estim_propuesto=entrada.ultimo_contador_facturado.valor,
        impresiones=0,
        fuente=fuente,
        metodo_detalle="Sin movimiento",
    )


def _t4_tal_cual(entrada: EstimacionInput, t4: LecturaRef) -> EstimacionResultado:
    return replace(
        _BASE,
        estim_propuesto=t4.valor,
        impresiones=t4.valor - entrada.ultimo_contador_facturado.valor,
        fuente="Backup_ConST",
        metodo_detalle="Backup con Servicio Técnico",
        t4_sin_revisar=not entrada.t4_revisado,
    )


def resolver_backup(entrada: EstimacionInput) -> EstimacionResultado:
    """Un Backup no tiene tasa de impresión representativa para proyectar
    (REGLAS_DE_NEGOCIO §5.1): con T4 válido se toma tal cual, sin regla de
    tres y sin ofrecer la opción de proyectar que sí se ofrece en el caso
    general sin par (CASOS_DE_PRUEBA §6 Caso F vs. Caso E)."""
    t4 = entrada.t4_mas_reciente
    if t4_es_valido(t4, entrada.fecha_ultimo_real_no_t4, entrada.fecha_objetivo):
        assert t4 is not None
        return _t4_tal_cual(entrada, t4)
    return _sin_movimiento(entrada, "Backup_SinST")


def resolver_en_transito(entrada: EstimacionInput) -> EstimacionResultado:
    return _sin_movimiento(entrada, "EnTransito")
