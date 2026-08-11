"""Tests del ciclo de vida de estados de Canal Directo (lista negra, nunca whitelist)."""

import pytest

from src.modules.insumos.domain.value_objects import cd_state


@pytest.mark.parametrize(
    "estado", [cd_state.PENDIENTE, cd_state.DESPACHADO, cd_state.REMITO_GENERADO]
)
def test_estados_conocidos_no_terminales_siguen_en_transito(estado: str) -> None:
    assert cd_state.is_in_transit(estado)


def test_estado_intermedio_desconocido_sigue_en_transito() -> None:
    """La regla es lista negra a propósito: un estado nuevo de CD no anticipado no debe
    hacer desaparecer el pedido de las vistas de seguimiento (bug original del legacy)."""
    assert cd_state.is_in_transit("En Preparación")


@pytest.mark.parametrize("estado", [cd_state.ENTREGADO, cd_state.ANULADO, cd_state.CANCELADO])
def test_estados_terminales_no_estan_en_transito(estado: str) -> None:
    assert not cd_state.is_in_transit(estado)


@pytest.mark.parametrize("estado", [None, ""])
def test_sin_estado_no_esta_en_transito(estado: str | None) -> None:
    assert not cd_state.is_in_transit(estado)


def test_entregado_no_libera_la_solicitud() -> None:
    """Entregado es cierre exitoso, no anulación — confundir RELEASE_STATES con
    INACTIVE_STATES es el bug fácil documentado en la caracterización (§8)."""
    assert cd_state.ENTREGADO not in cd_state.RELEASE_STATES
    assert {cd_state.ANULADO, cd_state.CANCELADO} == cd_state.RELEASE_STATES
