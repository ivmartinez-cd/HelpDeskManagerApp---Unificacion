"""REGLAS_DE_NEGOCIO §1 (real nunca se pisa) y §14 (interpolación hacia atrás
requiere confirmación manual obligatoria, decisión 2026-09-05)."""

from dataclasses import replace
from datetime import date

from src.modules.contadores.application.dtos.decision_operador_dto import (
    DecisionManualDto,
    DecisionOperadorDto,
)
from src.modules.contadores.application.dtos.equipo_proceso_dto import ClaseProceso
from src.modules.contadores.application.use_cases._resolver_resultado_final import (
    resolver_resultado_final,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

_AUTOMATICO_BASE = EstimacionResultado(
    estim_propuesto=40_200,
    impresiones=9_300,
    tipo_toma=14,
    fuente="Historia_Propia",
    metodo_detalle="Entre dos reales",
    requiere_confirmacion=True,
    semaforo="AMARILLO",
    borde_salto_imposible=False,
    coloreo=None,
    nota_operador=None,
    meses_sin_real_en_alerta=False,
    dias_par_pl=91,
    ajustado_por_receso=False,
    dias_receso_descontados=0,
    bloqueo_obligatorio=True,
)

_CLASE = ClaseProceso(
    clase="10",
    tecnologia="Mono",
    velocidad_ppm=45,
    ultimo_contador_facturado=LecturaRef(30_884, date(2026, 5, 1), 14),
)


def test_bloqueo_obligatorio_sin_decision_deja_la_fila_en_blanco() -> None:
    resultado = resolver_resultado_final(_CLASE, _AUTOMATICO_BASE, None)

    assert resultado.estim_propuesto is None
    assert resultado.tipo_toma is None
    assert resultado.fuente == "Pendiente"
    assert resultado.semaforo == "ROJO"


def test_bloqueo_obligatorio_con_nota_sigue_en_blanco() -> None:
    """Una nota es solo un comentario — no resuelve el bloqueo."""
    decision = DecisionOperadorDto(nota="revisar con el cliente")

    resultado = resolver_resultado_final(_CLASE, _AUTOMATICO_BASE, decision)

    assert resultado.estim_propuesto is None
    assert resultado.fuente == "Pendiente"


def test_decision_manual_desbloquea_y_gana() -> None:
    manual = DecisionManualDto(
        contador_propuesto=40_500, tipo_toma=14, fuente="Historia_Propia", metodo_detalle="Manual"
    )
    decision = DecisionOperadorDto(manual=manual)

    resultado = resolver_resultado_final(_CLASE, _AUTOMATICO_BASE, decision)

    assert resultado.estim_propuesto == 40_500
    assert resultado.requiere_confirmacion is False


def test_marcar_pendiente_explicito_tambien_gana() -> None:
    decision = DecisionOperadorDto(pendiente=True)

    resultado = resolver_resultado_final(_CLASE, _AUTOMATICO_BASE, decision)

    assert resultado.estim_propuesto is None
    assert resultado.metodo_detalle == "Marcado pendiente por el operador"


def test_sin_bloqueo_obligatorio_automatico_pasa_directo() -> None:
    automatico = replace(_AUTOMATICO_BASE, bloqueo_obligatorio=False, requiere_confirmacion=False)

    resultado = resolver_resultado_final(_CLASE, automatico, None)

    assert resultado.estim_propuesto == 40_200
