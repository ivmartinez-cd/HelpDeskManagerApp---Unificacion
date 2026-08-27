"""`/api/sla/incidentes-derivados` por HTTP (ver conftest.py de este paquete):
401/403, el envelope `Page[T]`, el orden por días descendente, el filtro por
PST del interior y por operador, y los 400 de `periodo` (Query y VO `Periodo`)."""

from __future__ import annotations

import uuid

import pytest

from tests.integration.router_testing import client
from tests.integration.sla.support import DERIVADOS, PAGE_KEYS, PERIODO


async def test_sin_sesion_devuelve_401() -> None:
    async with client() as c:
        response = await c.get(DERIVADOS, params={"periodo": PERIODO})

    assert response.status_code == 401


@pytest.mark.usefixtures("_sesion_sin_grant")
async def test_sesion_valida_sin_grant_devuelve_403() -> None:
    async with client() as c:
        response = await c.get(DERIVADOS, params={"periodo": PERIODO})

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.usefixtures("_sesion_view", "derivados_gateway")
async def test_listado_filtra_a_mis_pst_del_interior_mas_viejos_primero() -> None:
    async with client() as c:
        response = await c.get(DERIVADOS, params={"periodo": PERIODO})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == PAGE_KEYS
    assert body["total"] == 2
    assert [item["id_incidente"] for item in body["items"]] == [21, 20]
    assert set(body["items"][0]) == {
        "id_incidente", "fecha_ingreso", "tipo", "estado", "cliente", "sucursal",
        "nro_serie", "modelo", "tecnico", "id_tecnico", "operador", "dias_desde_ingreso",
        "demorado",
    }


@pytest.mark.usefixtures("_sesion_view", "derivados_gateway")
async def test_listado_operador_ajeno_no_ve_los_propios() -> None:
    async with client() as c:
        response = await c.get(
            DERIVADOS, params={"periodo": PERIODO, "operadorId": str(uuid.uuid4())}
        )

    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.usefixtures("_sesion_view", "derivados_gateway")
async def test_listado_size_fuera_de_rango_es_400() -> None:
    async with client() as c:
        response = await c.get(DERIVADOS, params={"periodo": PERIODO, "size": 0})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.usefixtures("_sesion_view", "derivados_gateway")
@pytest.mark.parametrize(
    ("periodo", "code"),
    [
        ("", "VALIDATION_ERROR"),
        ("199912", "VALIDATION_ERROR"),
        ("agosto", "VALIDATION_ERROR"),
        ("202613", "PERIODO_INVALIDO"),
    ],
)
async def test_periodo_invalido_es_400(periodo: str, code: str) -> None:
    async with client() as c:
        response = await c.get(DERIVADOS, params={"periodo": periodo})

    assert response.status_code == 400
    assert response.json()["code"] == code
