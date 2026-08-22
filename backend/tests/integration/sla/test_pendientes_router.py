"""`/api/sla/pendientes-a-cerrar` por HTTP (ver conftest.py de este paquete):
401/403 (view vs update), el contrato del resumen filtrado a los PST del
operador, el envelope `Page[T]` del listado (más viejos primero, filtro por
PST acotado a la cartera propia), el 400 de paginación y el refresh a demanda."""

from __future__ import annotations

import pytest

from tests.integration.router_testing import client
from tests.integration.sla.support import PAGE_KEYS, PEND, PST_AJENO, PST_PROPIO
from tests.unit.application.sla.fakes_pendientes import FakePendientesQueryGateway

# --- Autenticación / autorización ------------------------------------------


async def test_sin_sesion_devuelve_401() -> None:
    async with client() as c:
        response = await c.get(f"{PEND}/resumen")

    assert response.status_code == 401


@pytest.mark.usefixtures("_sesion_sin_grant")
@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", f"{PEND}/resumen"), ("GET", PEND), ("POST", f"{PEND}/actualizar")],
)
async def test_sesion_valida_sin_grant_devuelve_403(method: str, path: str) -> None:
    async with client() as c:
        response = await c.request(method, path)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.usefixtures("_sesion_view", "pendientes_gateway")
async def test_actualizar_con_solo_view_devuelve_403() -> None:
    async with client() as c:
        response = await c.post(f"{PEND}/actualizar")

    assert response.status_code == 403


# --- GET /resumen -------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "pendientes_gateway")
async def test_resumen_filtra_a_los_pst_del_operador() -> None:
    async with client() as c:
        response = await c.get(f"{PEND}/resumen")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"total", "por_prestador", "por_operador", "updated_at"}
    assert body["total"] == 2
    assert body["por_prestador"] == [
        {
            "id_tecnico": PST_PROPIO,
            "tecnico": "Tecnico Propio",
            "cantidad": 2,
            "ids_incidente": [10, 11],
            "operador_nombre": "Operador",
        }
    ]
    assert body["por_operador"] == [{"operador_nombre": "Operador", "cantidad": 2}]


# --- GET "" (listado paginado) ------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "pendientes_gateway")
async def test_listado_paginado_mas_viejos_primero_y_filtro_por_pst() -> None:
    async with client() as c:
        propios = await c.get(PEND, params={"page": 1, "size": 1})
        ajeno = await c.get(PEND, params={"prestadorId": PST_AJENO})

    assert propios.status_code == 200
    body = propios.json()
    assert set(body) == PAGE_KEYS
    assert (body["total"], body["page"], body["size"]) == (2, 1, 1)
    assert set(body["items"][0]) == {
        "id_incidente", "tecnico", "id_tecnico", "cliente", "sucursal", "modelo", "nro_serie",
        "fecha_ingreso", "fecha_finalizacion", "dias_en_estado",
    }
    assert body["items"][0]["id_incidente"] == 11  # 9 días en estado, antes que el de 3
    # Un PST fuera de la cartera propia no se puede espiar por query param.
    assert ajeno.json()["total"] == 0


@pytest.mark.usefixtures("_sesion_view", "pendientes_gateway")
async def test_listado_size_fuera_de_rango_es_400() -> None:
    async with client() as c:
        response = await c.get(PEND, params={"size": 0})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


# --- POST /actualizar -----------------------------------------------------------


@pytest.mark.usefixtures("_sesion_update", "pendientes_gateway")
async def test_actualizar_refresca_y_devuelve_resumen(
    pendientes_gateway: FakePendientesQueryGateway,
) -> None:
    async with client() as c:
        response = await c.post(f"{PEND}/actualizar")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert pendientes_gateway.meses_consultados == [6]
