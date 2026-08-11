from src.modules.sla.domain.entities.incidente_sla import (
    RESULTADO_CORRECTO,
    RESULTADO_VENCIDO,
)
from tests.unit.domain.sla.fakes import build_incidente


def test_es_vencido_cuando_el_resultado_es_vencido() -> None:
    assert build_incidente(1, "CD - Técnico", RESULTADO_VENCIDO).es_vencido


def test_no_es_vencido_cuando_el_resultado_es_correcto() -> None:
    assert not build_incidente(1, "CD - Técnico", RESULTADO_CORRECTO).es_vencido
