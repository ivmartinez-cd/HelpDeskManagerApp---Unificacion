import uuid

import pytest

from src.modules.auth.domain.entities.dashboard_prefs import (
    MAX_HIDDEN_CARDS,
    DashboardPrefs,
)
from src.modules.auth.domain.errors import InvalidDashboardPrefsError


def test_default_no_oculta_nada_y_abre_en_hoy() -> None:
    prefs = DashboardPrefs.default(uuid.uuid4())

    assert prefs.hidden_cards == ()
    assert prefs.initial_view == "hoy"


def test_acepta_ids_slug_y_vista_valida() -> None:
    prefs = DashboardPrefs(
        user_id=uuid.uuid4(),
        hidden_cards=("wati-pendientes", "sla-mes"),
        initial_view="seguimiento",
    )

    assert prefs.hidden_cards == ("wati-pendientes", "sla-mes")


@pytest.mark.parametrize("vista", ["", "HOY", "otra", "hoy "])
def test_rechaza_vista_desconocida(vista: str) -> None:
    with pytest.raises(InvalidDashboardPrefsError, match="vista inicial"):
        DashboardPrefs(user_id=uuid.uuid4(), hidden_cards=(), initial_view=vista)


@pytest.mark.parametrize("card", ["", "Turnos", "1abc", "a b", "x" * 65, "a/b"])
def test_rechaza_id_de_panel_invalido(card: str) -> None:
    with pytest.raises(InvalidDashboardPrefsError, match="id de panel"):
        DashboardPrefs(user_id=uuid.uuid4(), hidden_cards=(card,), initial_view="hoy")


def test_rechaza_repetidos_y_exceso() -> None:
    with pytest.raises(InvalidDashboardPrefsError, match="repetidos"):
        DashboardPrefs(user_id=uuid.uuid4(), hidden_cards=("a", "a"), initial_view="hoy")
    demasiados = tuple(f"c{i}" for i in range(MAX_HIDDEN_CARDS + 1))
    with pytest.raises(InvalidDashboardPrefsError, match="demasiados"):
        DashboardPrefs(user_id=uuid.uuid4(), hidden_cards=demasiados, initial_view="hoy")
