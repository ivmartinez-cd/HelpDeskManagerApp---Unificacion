"""Router de preventivos por HTTP, sin DB ni Siges: el gateway y los repos de
habilitaciones/coordenadas van en memoria (tests/unit/application/preventivos/
fakes.py) vía monkeypatch de los nombres que el router importa. Cubre 401/403
(view vs update), el catálogo de zonas paginado, la tabla y el mapa (Page +
sellos extra), los 400 de validación (zona faltante / excluida) y el ciclo
habilitar → 201 / repetido → 409 / deshabilitar → 204 / inexistente → 404."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta

import pytest

import src.modules.preventivos.presentation.preventivos_router as preventivos_router
from src.modules.preventivos.domain.entities.zona_parque import ZonaParque
from tests.integration.router_testing import client, install_session, uninstall_session
from tests.unit.application.preventivos.fakes import (
    FakeHabilitacionRepository,
    FakePreventivosQueryGateway,
    FakeSucursalCoordenadasRepository,
    build_equipo,
    build_habilitacion,
)

_PREFIX = "/api/preventivos"
_MODULE = "preventivos"
_PAGE_KEYS = {"items", "total", "page", "size"}


@pytest.fixture
def _sesion_view(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, (_MODULE, "view"))
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_update(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, (_MODULE, "view"), (_MODULE, "update"))
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_sin_grant(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, ("insumos", "view"))
    yield None
    uninstall_session()


@pytest.fixture
def habilitaciones(monkeypatch: pytest.MonkeyPatch) -> FakeHabilitacionRepository:
    repo = FakeHabilitacionRepository([build_habilitacion(2)])
    monkeypatch.setattr(
        preventivos_router, "SqlAlchemyHabilitacionRepository", lambda _db: repo
    )
    return repo


@pytest.fixture
def coordenadas(monkeypatch: pytest.MonkeyPatch) -> FakeSucursalCoordenadasRepository:
    repo = FakeSucursalCoordenadasRepository()
    monkeypatch.setattr(
        preventivos_router, "SqlAlchemySucursalCoordenadasRepository", lambda _db: repo
    )
    return repo


@pytest.fixture
def gateway(monkeypatch: pytest.MonkeyPatch) -> FakePreventivosQueryGateway:
    vencida = date.today() - timedelta(days=400)
    equipos = [
        build_equipo(1, id_sucursal=10, fecha_ultimo_preventivo=date.today()),
        build_equipo(2, id_sucursal=10, fecha_ultimo_preventivo=vencida),
        build_equipo(3, id_sucursal=20, zona="NORTE", latitud=None, longitud=None),
    ]
    zonas = [ZonaParque("SUR", 2), ZonaParque("NORTE", 1), ZonaParque("INTERIOR", 9)]
    gw = FakePreventivosQueryGateway(equipos, zonas)
    monkeypatch.setattr(preventivos_router, "get_preventivos_gateway", lambda: gw)
    monkeypatch.setattr(preventivos_router, "get_zonas_excluidas", lambda: ("INTERIOR",))
    return gw


# --- Autenticación / autorización ------------------------------------------


async def test_sin_sesion_devuelve_401() -> None:
    async with client() as c:
        response = await c.get(f"{_PREFIX}/zonas")

    assert response.status_code == 401


@pytest.mark.usefixtures("_sesion_sin_grant")
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", f"{_PREFIX}/zonas"),
        ("GET", f"{_PREFIX}/equipos?zona=SUR"),
        ("GET", f"{_PREFIX}/mapa?zona=SUR"),
        ("POST", f"{_PREFIX}/equipos/1/habilitar"),
        ("DELETE", f"{_PREFIX}/equipos/1/habilitar"),
    ],
)
async def test_sesion_valida_sin_grant_devuelve_403(method: str, path: str) -> None:
    async with client() as c:
        response = await c.request(method, path, json={})

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.usefixtures("_sesion_view", "habilitaciones")
@pytest.mark.parametrize("method", ["POST", "DELETE"])
async def test_habilitar_con_solo_view_devuelve_403(method: str) -> None:
    async with client() as c:
        response = await c.request(method, f"{_PREFIX}/equipos/1/habilitar", json={})

    assert response.status_code == 403


# --- GET /zonas ---------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "gateway")
async def test_zonas_excluye_configuradas_y_pagina() -> None:
    async with client() as c:
        response = await c.get(f"{_PREFIX}/zonas", params={"page": 1, "size": 10})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == _PAGE_KEYS
    assert (body["total"], body["page"], body["size"]) == (2, 1, 10)
    assert body["items"] == [
        {"zona": "NORTE", "maquinas_activas": 1},
        {"zona": "SUR", "maquinas_activas": 2},
    ]


# --- GET /equipos -------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "gateway", "habilitaciones")
async def test_equipos_devuelve_page_con_sello_de_frescura() -> None:
    async with client() as c:
        response = await c.get(f"{_PREFIX}/equipos", params={"zona": "SUR"})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == _PAGE_KEYS | {"consultado_en"}
    assert body["total"] == 2
    vencido = body["items"][0]  # vencidos primero
    assert set(vencido) == {
        "id_maquina", "serie", "modelo", "cliente", "sucursal", "zona", "frecuencia_dias",
        "fecha_ultimo_preventivo", "proximo_vencimiento", "estado", "dias_vencido",
        "fecha_tentativa", "habilitacion",
    }
    assert vencido["id_maquina"] == 2
    assert vencido["estado"] == "vencido"
    assert vencido["habilitacion"]["habilitado_por"] == "Ana Prueba"
    assert body["items"][1]["habilitacion"] is None


@pytest.mark.usefixtures("_sesion_view", "gateway", "habilitaciones")
async def test_equipos_filtra_por_habilitado() -> None:
    async with client() as c:
        response = await c.get(f"{_PREFIX}/equipos", params={"zona": "SUR", "habilitado": True})

    assert response.status_code == 200
    assert [e["id_maquina"] for e in response.json()["items"]] == [2]


@pytest.mark.usefixtures("_sesion_view", "gateway", "habilitaciones")
async def test_equipos_sin_zona_es_400() -> None:
    async with client() as c:
        response = await c.get(f"{_PREFIX}/equipos")

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.usefixtures("_sesion_view", "gateway", "habilitaciones")
async def test_equipos_zona_excluida_es_400_sin_consultar_siges(
    gateway: FakePreventivosQueryGateway,
) -> None:
    async with client() as c:
        response = await c.get(f"{_PREFIX}/equipos", params={"zona": "INTERIOR"})

    assert response.status_code == 400
    assert response.json()["code"] == "ZONA_INVALIDA"
    assert gateway.zonas_consultadas == []


# --- GET /mapa ----------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "gateway", "habilitaciones", "coordenadas")
async def test_mapa_colapsa_por_sucursal_y_cuenta_sin_ubicar() -> None:
    async with client() as c:
        sur = await c.get(f"{_PREFIX}/mapa", params={"zona": "SUR"})
        norte = await c.get(f"{_PREFIX}/mapa", params={"zona": "NORTE"})

    assert sur.status_code == 200
    body = sur.json()
    assert set(body) == _PAGE_KEYS | {"consultado_en", "sin_ubicar"}
    assert body["total"] == 1
    punto = body["items"][0]
    assert set(punto) == {
        "id_sucursal", "cliente", "sucursal", "zona", "domicilio", "latitud", "longitud",
        "ubicado", "cant_maquinas", "cant_habilitadas", "peor_estado", "fecha_vencido_min",
        "fecha_tentativa_min", "distribucion",
    }
    assert (punto["id_sucursal"], punto["cant_maquinas"], punto["cant_habilitadas"]) == (10, 2, 1)
    assert punto["peor_estado"] == "vencido"
    assert body["sin_ubicar"] == 0
    assert norte.json()["sin_ubicar"] == 1


# --- POST/DELETE /equipos/{id}/habilitar ---------------------------------------


@pytest.mark.usefixtures("_sesion_update", "habilitaciones")
async def test_habilitar_crea_marca_y_repetir_es_409(
    habilitaciones: FakeHabilitacionRepository,
) -> None:
    async with client() as c:
        creado = await c.post(f"{_PREFIX}/equipos/31852/habilitar", json={"nota": " urgente "})
        repetido = await c.post(f"{_PREFIX}/equipos/31852/habilitar", json={})

    assert creado.status_code == 201
    body = creado.json()
    assert set(body) == {"habilitado_por", "habilitado_en", "nota"}
    assert body["habilitado_por"] == "Operador"
    assert body["nota"] == "urgente"
    assert repetido.status_code == 409
    assert repetido.json()["code"] == "HABILITACION_YA_ACTIVA"
    assert any(h.siges_maquina_id == 31852 and h.activa for h in habilitaciones.habilitaciones)


@pytest.mark.usefixtures("_sesion_update", "habilitaciones")
async def test_habilitar_nota_demasiado_larga_es_400() -> None:
    async with client() as c:
        response = await c.post(f"{_PREFIX}/equipos/1/habilitar", json={"nota": "x" * 301})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.usefixtures("_sesion_update", "habilitaciones")
async def test_deshabilitar_devuelve_204_y_luego_404(
    habilitaciones: FakeHabilitacionRepository,
) -> None:
    async with client() as c:
        primero = await c.delete(f"{_PREFIX}/equipos/2/habilitar")
        segundo = await c.delete(f"{_PREFIX}/equipos/2/habilitar")

    assert primero.status_code == 204
    assert habilitaciones.habilitaciones[0].activa is False
    assert habilitaciones.habilitaciones[0].deshabilitado_por == "Operador"
    assert segundo.status_code == 404
    assert segundo.json()["code"] == "HABILITACION_NO_ENCONTRADA"
