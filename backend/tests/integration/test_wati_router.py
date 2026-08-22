"""Router de wati/pendientes por HTTP, sin DB ni WATI real: el repo de
conversaciones y el gateway van en memoria (tests/unit/domain/wati/fakes.py)
vía monkeypatch de los factories importados en el router. Cubre 401/403,
el contrato de `/resumen`, el envelope `Page[T]` del listado, el 400 de
paginación y el ciclo `/actualizar` (solo `update`, commitea la sesión)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

import src.modules.wati.presentation.pendientes_router as pendientes_router
from src.modules.wati.application.use_cases.get_pendientes_resumen import GetPendientesResumen
from src.modules.wati.application.use_cases.list_pendientes import ListPendientes
from src.modules.wati.application.use_cases.sync_conversaciones import SyncConversaciones
from src.modules.wati.domain.entities.conversacion import ConversacionWati
from src.modules.wati.domain.value_objects.evento import ContactoWati
from tests.integration.router_testing import (
    FakeDb,
    client,
    install_session,
    uninstall_session,
)
from tests.unit.domain.wati.fakes import (
    FakeConversacionRepository,
    FakeWatiGateway,
    en,
    msg_cliente,
)

_PREFIX = "/api/wati/pendientes"
_MODULE = "wati"
_AHORA = en(60)


def _conversacion(wa_id: str, *, minutos_cliente: int, operador: str | None) -> ConversacionWati:
    return ConversacionWati(
        wa_id=wa_id,
        nombre=f"Cliente {wa_id}",
        conversation_id="c1",
        ticket_id="t1",
        operador_nombre=operador,
        operador_email=None,
        ultimo_mensaje_cliente_at=en(minutos_cliente),
        esperando_desde=en(minutos_cliente),
        ultima_respuesta_at=None,
        ultimo_bot_at=None,
        cerrada_at=None,
        bot_activo=False,
        ultimo_texto_cliente="hola",
        sincronizado_at=_AHORA,
    )


@pytest.fixture
def fake_db() -> FakeDb:
    return FakeDb()


@pytest.fixture
def _sesion_view(monkeypatch: pytest.MonkeyPatch, fake_db: FakeDb) -> Iterator[None]:
    install_session(monkeypatch, (_MODULE, "view"), db=fake_db)
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_update(monkeypatch: pytest.MonkeyPatch, fake_db: FakeDb) -> Iterator[None]:
    install_session(monkeypatch, (_MODULE, "view"), (_MODULE, "update"), db=fake_db)
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_sin_grant(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, ("insumos", "view"))
    yield None
    uninstall_session()


@pytest.fixture
def repo(monkeypatch: pytest.MonkeyPatch) -> FakeConversacionRepository:
    repo = FakeConversacionRepository()
    repo.rows["111"] = _conversacion("111", minutos_cliente=45, operador="MDA")
    repo.rows["222"] = _conversacion("222", minutos_cliente=20, operador=None)
    listar = ListPendientes(repo, reloj=lambda: _AHORA)
    monkeypatch.setattr(pendientes_router, "build_list_pendientes", lambda _db: listar)
    monkeypatch.setattr(
        pendientes_router,
        "build_get_pendientes_resumen",
        lambda _db: GetPendientesResumen(repo, listar),
    )
    return repo


# --- Autenticación / autorización ------------------------------------------


async def test_sin_sesion_devuelve_401() -> None:
    async with client() as c:
        response = await c.get(f"{_PREFIX}/resumen")

    assert response.status_code == 401


@pytest.mark.usefixtures("_sesion_sin_grant")
@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", f"{_PREFIX}/resumen"), ("GET", _PREFIX), ("POST", f"{_PREFIX}/actualizar")],
)
async def test_sesion_valida_sin_grant_devuelve_403(method: str, path: str) -> None:
    async with client() as c:
        response = await c.request(method, path)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.usefixtures("_sesion_view", "repo")
async def test_actualizar_con_solo_view_devuelve_403() -> None:
    """Forzar un ciclo contra WATI consume cuota: exige `update`, no `view`."""
    async with client() as c:
        response = await c.post(f"{_PREFIX}/actualizar")

    assert response.status_code == 403


# --- GET /resumen -------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "repo")
async def test_resumen_devuelve_conteos_y_desglose_por_operador() -> None:
    async with client() as c:
        response = await c.get(f"{_PREFIX}/resumen")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "total", "sin_asignar", "max_minutos_esperando", "por_operador",
        "sincronizado_at", "inbox_url",
    }
    assert body["total"] == 2
    assert body["sin_asignar"] == 1
    assert body["max_minutos_esperando"] == 40
    assert body["por_operador"] == [
        {"operador": "MDA", "cantidad": 1},
        {"operador": "Sin asignar", "cantidad": 1},
    ]
    assert body["sincronizado_at"] is not None


# --- GET "" (listado paginado) ------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "repo")
async def test_listar_pendientes_paginado_de_la_mas_antigua_a_la_mas_nueva() -> None:
    async with client() as c:
        response = await c.get(_PREFIX, params={"page": 1, "size": 1})

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["page"], body["size"]) == (2, 1, 1)
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert set(item) == {
        "wa_id", "nombre", "operador_nombre", "operador_email", "sin_asignar",
        "esperando_desde", "minutos_esperando", "ultimo_mensaje_cliente_at",
        "ultimo_texto_cliente",
    }
    assert item["wa_id"] == "222"
    assert item["sin_asignar"] is True
    assert item["minutos_esperando"] == 40


@pytest.mark.usefixtures("_sesion_view", "repo")
async def test_listar_con_size_fuera_de_rango_es_400() -> None:
    async with client() as c:
        response = await c.get(_PREFIX, params={"size": 201})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


# --- POST /actualizar ---------------------------------------------------------


@pytest.mark.usefixtures("_sesion_update")
async def test_actualizar_sincroniza_contra_el_gateway_y_commitea(
    monkeypatch: pytest.MonkeyPatch, fake_db: FakeDb
) -> None:
    gateway = FakeWatiGateway(
        contactos=[ContactoWati(wa_id="111", nombre="Cliente 111", last_updated=en(50))],
        eventos={"111": [msg_cliente(45)]},
    )
    repo = FakeConversacionRepository()
    sync = SyncConversaciones(gateway, repo, reloj=lambda: _AHORA)
    monkeypatch.setattr(pendientes_router, "build_sync_conversaciones", lambda _db: sync)

    async with client() as c:
        response = await c.post(f"{_PREFIX}/actualizar")

    assert response.status_code == 200
    assert response.json() == {"contactos_revisados": 1, "esperando": 1, "descartados": 0}
    assert gateway.consultados == ["111"]
    assert fake_db.commits == 1
