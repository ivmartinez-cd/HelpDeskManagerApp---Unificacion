"""`/api/sla/mesa-de-ayuda` por HTTP (ver conftest.py de este paquete): 401/403,
el envelope `Page[T]`, el orden por días descendente y el filtro por operador."""

from __future__ import annotations

import pytest

from tests.integration.router_testing import client
from tests.integration.sla.support import MESA, PAGE_KEYS


async def test_sin_sesion_devuelve_401() -> None:
    async with client() as c:
        response = await c.get(MESA)

    assert response.status_code == 401


@pytest.mark.usefixtures("_sesion_sin_grant")
async def test_sesion_valida_sin_grant_devuelve_403() -> None:
    async with client() as c:
        response = await c.get(MESA)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.usefixtures("_sesion_view", "mesa_ayuda_gateway")
async def test_listado_paginado_mas_viejos_primero() -> None:
    async with client() as c:
        response = await c.get(MESA)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == PAGE_KEYS
    assert body["total"] == 2
    assert [item["id_incidente"] for item in body["items"]] == [101, 100]
    assert set(body["items"][0]) == {
        "id_incidente", "fecha_ingreso", "tipo", "estado", "cliente", "sucursal",
        "nro_serie", "modelo", "operador_login", "operador", "dias_transcurridos", "demorado",
    }


@pytest.mark.usefixtures("_sesion_view", "mesa_ayuda_gateway")
async def test_filtra_por_operador() -> None:
    async with client() as c:
        response = await c.get(MESA, params={"operador": "vipaez"})

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id_incidente"] == 100


@pytest.mark.usefixtures("_sesion_view", "mesa_ayuda_gateway")
async def test_listado_size_fuera_de_rango_es_400() -> None:
    async with client() as c:
        response = await c.get(MESA, params={"size": 0})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
