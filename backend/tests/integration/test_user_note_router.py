"""`/api/me/nota` por HTTP (ADR-033): solo sesión, user_id de la identidad,
PUT idempotente, tope de longitud como error de dominio (400, no 500)."""

from __future__ import annotations

from uuid import UUID

import pytest

import src.modules.auth.presentation.user_note_router as router_mod
from src.modules.auth.domain.entities.user_note import MAX_NOTE_CHARS, UserNote
from tests.integration.router_testing import client, install_session, uninstall_session

URL = "/api/me/nota"


class FakeRepo:
    rows: dict[UUID, UserNote] = {}

    def __init__(self, _db: object) -> None:
        pass

    async def get(self, user_id: UUID) -> UserNote | None:
        return self.rows.get(user_id)

    async def upsert(self, note: UserNote) -> UserNote:
        self.rows[note.user_id] = note
        return note


@pytest.fixture(autouse=True)
def _repo(monkeypatch: pytest.MonkeyPatch):
    FakeRepo.rows = {}
    monkeypatch.setattr(router_mod, "SqlAlchemyUserNoteRepository", FakeRepo)
    yield
    uninstall_session()


async def test_sin_sesion_es_401() -> None:
    async with client() as c:
        assert (await c.get(URL)).status_code == 401
        assert (await c.put(URL, json={"content": "x"})).status_code == 401


async def test_get_sin_nota_devuelve_vacia_con_el_tope(monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch)
    async with client() as c:
        response = await c.get(URL)

    assert response.status_code == 200
    assert response.json() == {"content": "", "updatedAt": None, "maxChars": MAX_NOTE_CHARS}


async def test_put_guarda_para_la_sesion_y_get_lo_devuelve(monkeypatch: pytest.MonkeyPatch) -> None:
    identity = install_session(monkeypatch)
    async with client() as c:
        puesto = await c.put(URL, json={"content": "probando"})
        leido = await c.get(URL)

    assert puesto.status_code == 200 and puesto.json()["content"] == "probando"
    assert leido.json()["content"] == "probando"
    assert set(FakeRepo.rows) == {identity.user.id}


async def test_put_demasiado_largo_es_400_no_500(monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch)
    async with client() as c:
        largo = await c.put(URL, json={"content": "x" * (MAX_NOTE_CHARS + 1)})
        extra = await c.put(URL, json={"content": "ok", "otro": 1})

    # El tope lo corta el schema (borde) con el envelope de validación.
    assert (largo.status_code, largo.json()["code"]) == (400, "VALIDATION_ERROR")
    assert (extra.status_code, extra.json()["code"]) == (400, "VALIDATION_ERROR")
    assert FakeRepo.rows == {}
