"""`GET /api/insumos/despachados/{guia}/reclamo-oca` por HTTP, sin DB ni OCA: el caso de
uso real sobre los fakes en memoria (`MundoConsulta`) y los contactos por defecto de
settings (26108… = cuenta 434324, 211… = 443913). Cubre permisos, 400, 404 y el wire en
camelCase."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

import src.modules.insumos.presentation.despachados_acciones_router as acciones_router
from src.modules.insumos.application.use_cases.despachados.consultas_despachos import (
    ObtenerDetalleDespacho,
)
from src.modules.insumos.application.use_cases.despachados.reclamo_oca import (
    PrepararReclamoOca,
)
from src.modules.insumos.presentation.dependencies.despachados import reglas_contacto_reclamo
from tests.integration.router_testing import client, install_session, uninstall_session
from tests.unit.application.insumos.despachados.fakes_consulta_despachos import (
    CONFIG,
    MundoConsulta,
)
from tests.unit.application.insumos.despachados.fakes_despachados import (
    despacho,
    envio,
    estado_oca,
)

_BASE = "/api/insumos/despachados"
_GUIA_CORREO = "2610800000000000001"
_GUIA_CLIENTE = "2110000000000000001"
_GUIA_SIN_REGLA = "3867500000000000001"


@pytest.fixture
def _sesion_view(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, ("insumos", "view"))
    yield None
    uninstall_session()


@pytest.fixture
def _sesion_update(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    install_session(monkeypatch, ("insumos", "view"), ("insumos", "update"))
    yield None
    uninstall_session()


@pytest.fixture
def mundo(monkeypatch: pytest.MonkeyPatch) -> MundoConsulta:
    mundo = MundoConsulta()
    for guia in (_GUIA_CORREO, _GUIA_CLIENTE, _GUIA_SIN_REGLA):
        mundo.envios.envios[guia] = envio(guia, estado_oca=estado_oca(guia))
        mundo.remitos.guardados.append(despacho(guia))
    reglas = reglas_contacto_reclamo()
    monkeypatch.setattr(
        acciones_router,
        "build_preparar_reclamo_oca",
        lambda _db: PrepararReclamoOca(ObtenerDetalleDespacho(mundo.ports(), CONFIG), reglas),
    )
    return mundo


def _url(guia: str) -> str:
    return f"{_BASE}/{guia}/reclamo-oca"


async def test_sin_sesion_devuelve_401() -> None:
    async with client() as c:
        response = await c.get(_url(_GUIA_CORREO))

    assert response.status_code == 401


@pytest.mark.usefixtures("_sesion_view", "mundo")
async def test_con_solo_view_devuelve_403() -> None:
    async with client() as c:
        response = await c.get(_url(_GUIA_CORREO))

    assert response.status_code == 403


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_guia_26108_trae_el_contacto_de_oca_correo_en_camel_case() -> None:
    async with client() as c:
        response = await c.get(_url(_GUIA_CORREO))

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"guia", "operativa", "contacto", "comentario"}
    assert (body["guia"], body["operativa"]) == (_GUIA_CORREO, "434324")
    assert body["contacto"] == {
        "nombre": "Canal Directo",
        "apellido": "Soluciones de Impresión",
        "empresa": "Canal Directo Soluciones de Impresión",
        "email": "ocacdsisa@canaldirecto.com.ar",
        "cuit": "30709381101",
        "telefono": "",
    }
    assert body["comentario"].startswith(f"Reclamo por el envío {_GUIA_CORREO}.\n")


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_guia_211_trae_el_contacto_de_oca_cliente() -> None:
    async with client() as c:
        response = await c.get(_url(_GUIA_CLIENTE))

    contacto = response.json()["contacto"]
    assert (contacto["empresa"], contacto["cuit"]) == ("Canal Directo SA", "30683465840")


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_guia_sin_regla_devuelve_contacto_null() -> None:
    async with client() as c:
        response = await c.get(_url(_GUIA_SIN_REGLA))

    assert response.status_code == 200
    assert response.json()["contacto"] is None


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_guia_no_seguida_devuelve_404() -> None:
    async with client() as c:
        response = await c.get(_url("9999999999999999999"))

    assert response.status_code == 404
    assert response.json()["code"] == "ENVIO_DESPACHO_NO_ENCONTRADO"


@pytest.mark.usefixtures("_sesion_update", "mundo")
async def test_guia_mal_formada_devuelve_400() -> None:
    async with client() as c:
        response = await c.get(_url("123"))

    assert response.status_code == 400
