"""`/api/me/inicio-prefs` por HTTP (ADR-033): solo sesión, user_id de la
identidad, PUT idempotente. Repo monkeypatcheado con un fake en memoria."""

from __future__ import annotations

from uuid import UUID

import pytest

import src.modules.auth.presentation.dashboard_prefs_router as router_mod
from src.modules.auth.domain.entities.dashboard_prefs import DashboardPrefs
from tests.integration.router_testing import client, install_session, uninstall_session

URL = "/api/me/inicio-prefs"


class FakeRepo:
    rows: dict[UUID, DashboardPrefs] = {}

    def __init__(self, _db: object) -> None:
        pass

    async def get(self, user_id: UUID) -> DashboardPrefs | None:
        return self.rows.get(user_id)

    async def upsert(self, prefs: DashboardPrefs) -> DashboardPrefs:
        self.rows[prefs.user_id] = prefs
        return prefs


@pytest.fixture(autouse=True)
def _repo(monkeypatch: pytest.MonkeyPatch):
    FakeRepo.rows = {}
    monkeypatch.setattr(router_mod, "SqlAlchemyDashboardPrefsRepository", FakeRepo)
    yield
    uninstall_session()


async def test_sin_sesion_es_401() -> None:
    async with client() as c:
        assert (await c.get(URL)).status_code == 401
        assert (await c.put(URL, json={"hiddenCards": [], "initialView": "hoy"})).status_code == 401


async def test_get_sin_preferencias_devuelve_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch)
    async with client() as c:
        response = await c.get(URL)

    assert response.status_code == 200
    assert response.json() == {"hiddenCards": [], "initialView": "hoy"}


async def test_put_guarda_para_el_usuario_de_la_sesion_y_get_lo_devuelve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity = install_session(monkeypatch)
    body = {"hiddenCards": ["wati-pendientes", "sla-mes"], "initialView": "seguimiento"}
    async with client() as c:
        puesto = await c.put(URL, json=body)
        leido = await c.get(URL)

    assert puesto.status_code == 200 and puesto.json() == body
    assert leido.json() == body
    assert set(FakeRepo.rows) == {identity.user.id}


async def test_put_invalido_es_400_con_codigo_de_dominio(monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch)
    async with client() as c:
        vista = await c.put(URL, json={"hiddenCards": [], "initialView": "otra"})
        card = await c.put(URL, json={"hiddenCards": ["Mayus"], "initialView": "hoy"})
        extra = await c.put(URL, json={"hiddenCards": [], "initialView": "hoy", "x": 1})

    assert (vista.status_code, vista.json()["code"]) == (400, "INVALID_DASHBOARD_PREFS")
    assert (card.status_code, card.json()["code"]) == (400, "INVALID_DASHBOARD_PREFS")
    assert (extra.status_code, extra.json()["code"]) == (400, "VALIDATION_ERROR")
    assert FakeRepo.rows == {}
