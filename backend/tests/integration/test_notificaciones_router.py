"""Router de notificaciones por HTTP, sin DB: exige sesión y le pasa al repo
las audiencias del usuario logueado (None = superadmin, ve todas)."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest

import src.modules.notificaciones.presentation.notificaciones_router as r
from src.modules.notificaciones.domain.entities.notificacion import Notificacion
from tests.integration.router_testing import client, install_session, uninstall_session


class _FakeRepo:
    llamadas: list[dict[str, Any]] = []

    def __init__(self, _db: object) -> None:
        pass

    async def listar(self, usuario_id: uuid.UUID, audiencias: Any, **kw: Any) -> Any:
        self.llamadas.append({"audiencias": audiencias, **kw})
        n = Notificacion(uuid.uuid4(), "t", "c", "/sla", datetime.now(UTC), False)
        return [n], 7

    async def marcar_leidas(self, usuario_id: uuid.UUID, audiencias: Any, ids: Any) -> int:
        self.llamadas.append({"audiencias": audiencias, "ids": ids})
        return 2


@pytest.fixture(autouse=True)
def _repo(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    _FakeRepo.llamadas = []
    monkeypatch.setattr(r, "SqlAlchemyNotificacionRepository", _FakeRepo)
    yield
    uninstall_session()


async def test_sin_sesion_da_401() -> None:
    async with client() as c:
        assert (await c.get("/api/notificaciones")).status_code == 401


async def test_lista_con_las_audiencias_del_usuario(monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch, ("sla", "view"))
    async with client() as c:
        resp = await c.get("/api/notificaciones?solo_no_leidas=true&page=2&size=5")

    assert resp.status_code == 200
    assert resp.json()["total"] == 7
    llamada = _FakeRepo.llamadas[0]
    assert llamada["audiencias"] == frozenset({"permiso:sla.view"})
    assert (llamada["solo_no_leidas"], llamada["offset"], llamada["limit"]) == (True, 5, 5)


async def test_superadmin_ve_todas(monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch, superadmin=True)
    async with client() as c:
        await c.post("/api/notificaciones/marcar-leidas", json={})

    assert _FakeRepo.llamadas[0] == {"audiencias": None, "ids": None}


async def test_marcar_leidas_por_id(monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch)
    ids = [str(uuid.uuid4())]
    async with client() as c:
        resp = await c.post("/api/notificaciones/marcar-leidas", json={"ids": ids})

    assert resp.json() == {"actualizadas": 2}
    assert [str(i) for i in _FakeRepo.llamadas[0]["ids"]] == ids
