"""La entidad Resolucion y sus decisiones válidas — vocabulario portado del
legacy (aprobar / solicitar_correccion / ignorar / escalar)."""

import uuid
from datetime import UTC, datetime

from src.modules.liquidaciones.domain.entities.resolucion import (
    DECISION_APROBAR,
    DECISION_ESCALAR,
    DECISION_IGNORAR,
    DECISION_SOLICITAR_CORRECCION,
    Resolucion,
)


def test_el_vocabulario_de_decisiones_es_el_del_legacy() -> None:
    assert {
        DECISION_APROBAR,
        DECISION_SOLICITAR_CORRECCION,
        DECISION_IGNORAR,
        DECISION_ESCALAR,
    } == {"aprobar", "solicitar_correccion", "ignorar", "escalar"}


def test_resolucion_es_un_registro_inmutable_de_la_decision() -> None:
    resolucion = Resolucion(
        id=uuid.uuid4(),
        alerta_id=uuid.uuid4(),
        decision=DECISION_APROBAR,
        justificacion="dentro del tarifario vigente",
        comentario=None,
        fecha=datetime(2026, 8, 12, tzinfo=UTC),
    )
    assert resolucion.decision == DECISION_APROBAR
    assert resolucion.justificacion == "dentro del tarifario vigente"
