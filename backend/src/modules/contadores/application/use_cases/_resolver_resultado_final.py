"""Prioridad real > decisión manual > pendiente > nota (REGLAS_DE_NEGOCIO §1:
un dato real nunca se pisa) — compartida por el tablero
(`get_tablero_proyeccion.py`) y el export a SiGes, para que ambos muestren
siempre el mismo resultado de un equipo/clase."""

from dataclasses import replace

from src.modules.contadores.application.dtos.decision_operador_dto import (
    DecisionManualDto,
    DecisionOperadorDto,
)
from src.modules.contadores.application.dtos.equipo_proceso_dto import ClaseProceso
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

_RESULTADO_PENDIENTE_POR_OPERADOR = EstimacionResultado(
    estim_propuesto=None,
    impresiones=None,
    tipo_toma=None,
    fuente="Pendiente",
    metodo_detalle="Marcado pendiente por el operador",
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

_RESULTADO_BLOQUEADO_POR_INTERPOLACION = EstimacionResultado(
    estim_propuesto=None,
    impresiones=None,
    tipo_toma=None,
    fuente="Pendiente",
    metodo_detalle="Interpolación hacia atrás: requiere confirmación manual antes de facturar",
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


def resolver_resultado_final(
    clase: ClaseProceso, automatico: EstimacionResultado, decision: DecisionOperadorDto | None
) -> EstimacionResultado:
    if clase.ya_real:
        return _resultado_real(clase, automatico)
    if decision and decision.pendiente:
        return _RESULTADO_PENDIENTE_POR_OPERADOR
    if decision and decision.manual:
        return _resultado_de_manual(decision.manual, clase, automatico)
    if automatico.bloqueo_obligatorio:
        return _RESULTADO_BLOQUEADO_POR_INTERPOLACION
    if decision and decision.nota:
        return replace(automatico, requiere_confirmacion=True)
    return automatico


def _resultado_real(clase: ClaseProceso, automatico: EstimacionResultado) -> EstimacionResultado:
    impresiones = (clase.valor_real_cargado or 0) - clase.ultimo_contador_facturado.valor
    return replace(
        automatico,
        estim_propuesto=clase.valor_real_cargado,
        impresiones=impresiones,
        tipo_toma=clase.ultimo_contador_facturado.tipo_toma,
        requiere_confirmacion=False,
        detalle_parque=None,
    )


def _impresiones_de_manual(manual: DecisionManualDto, clase: ClaseProceso) -> float | None:
    if manual.contador_propuesto is None:
        return None
    return manual.contador_propuesto - clase.ultimo_contador_facturado.valor


def _resultado_de_manual(
    manual: DecisionManualDto, clase: ClaseProceso, automatico: EstimacionResultado
) -> EstimacionResultado:
    """Limpia el detalle del cálculo automático (parque / P-L) — pertenece a
    un `fuente`/método distinto al elegido a mano (REGLAS_DE_NEGOCIO §8)."""
    return replace(
        automatico,
        estim_propuesto=manual.contador_propuesto,
        impresiones=_impresiones_de_manual(manual, clase),
        tipo_toma=manual.tipo_toma,
        fuente=manual.fuente,
        metodo_detalle=manual.metodo_detalle,
        requiere_confirmacion=False,
        detalle_parque=None,
        dias_par_pl=None,
        tasa_diaria=None,
        dias_proyectados=None,
    )
