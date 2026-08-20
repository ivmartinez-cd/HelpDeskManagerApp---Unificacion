from src.modules.liquidaciones.domain.entities.incidente import (
    ESTADO_VALIDACION_CON_ALERTAS,
    ESTADO_VALIDACION_OK,
)
from src.modules.liquidaciones.domain.services.triage_alertas import recalcular_estado_incidente


def test_ok_cuando_todas_resueltas_o_descartadas():
    assert recalcular_estado_incidente(["resuelta", "descartada"]) == ESTADO_VALIDACION_OK


def test_con_alertas_si_queda_una_pendiente():
    assert (
        recalcular_estado_incidente(["resuelta", "pendiente"]) == ESTADO_VALIDACION_CON_ALERTAS
    )


def test_con_alertas_si_queda_una_en_revision():
    assert (
        recalcular_estado_incidente(["descartada", "en_revision"])
        == ESTADO_VALIDACION_CON_ALERTAS
    )


def test_con_alertas_si_no_hay_alertas():
    assert recalcular_estado_incidente([]) == ESTADO_VALIDACION_CON_ALERTAS
