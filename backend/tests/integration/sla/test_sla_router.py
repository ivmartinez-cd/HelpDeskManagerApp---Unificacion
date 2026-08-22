"""`/api/sla` por HTTP (ver conftest.py de este paquete): 401/403 (view vs
update), el contrato del resumen, los 400 de `periodo` (Query y VO `Periodo`),
el envelope `Page[T]` de incidentes vencidos con el filtro por operador y el
refresh a demanda."""

from __future__ import annotations

import uuid

import pytest

from tests.integration.router_testing import client
from tests.integration.sla.support import PAGE_KEYS, PERIODO, SLA
from tests.unit.domain.sla.fakes import FakeSlaQueryGateway

# --- Autenticación / autorización ------------------------------------------


async def test_sin_sesion_devuelve_401() -> None:
    async with client() as c:
        response = await c.get(f"{SLA}/resumen", params={"periodo": PERIODO})

    assert response.status_code == 401


@pytest.mark.usefixtures("_sesion_sin_grant")
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", f"{SLA}/resumen?periodo={PERIODO}"),
        ("GET", f"{SLA}/incidentes-vencidos?periodo={PERIODO}"),
        ("POST", f"{SLA}/actualizar?periodo={PERIODO}"),
    ],
)
async def test_sesion_valida_sin_grant_devuelve_403(method: str, path: str) -> None:
    async with client() as c:
        response = await c.request(method, path)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.usefixtures("_sesion_view", "sla_gateway")
async def test_actualizar_con_solo_view_devuelve_403() -> None:
    """El refresh en vivo contra MERCURIO exige `update`, no `view`."""
    async with client() as c:
        response = await c.post(f"{SLA}/actualizar", params={"periodo": PERIODO})

    assert response.status_code == 403


# --- GET /resumen -------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "sla_gateway")
async def test_resumen_devuelve_cumplimiento_del_periodo() -> None:
    async with client() as c:
        response = await c.get(f"{SLA}/resumen", params={"periodo": PERIODO})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "periodo", "total", "correctos", "vencidos", "pct_correctos", "pct_vencidos",
        "vencidos_por_tecnico", "updated_at",
    }
    assert (body["periodo"], body["total"], body["correctos"], body["vencidos"]) == (
        PERIODO, 3, 1, 2
    )
    assert {t["tecnico"]: t["cantidad"] for t in body["vencidos_por_tecnico"]} == {
        "Tecnico Propio": 1, "Tecnico Ajeno": 1
    }


@pytest.mark.usefixtures("_sesion_view", "sla_gateway")
@pytest.mark.parametrize(
    ("periodo", "code"),
    [
        ("", "VALIDATION_ERROR"),
        ("199912", "VALIDATION_ERROR"),
        ("agosto", "VALIDATION_ERROR"),
        # Pasa el rango del Query pero no es un mes: lo rechaza el VO `Periodo`.
        ("202613", "PERIODO_INVALIDO"),
    ],
)
async def test_resumen_periodo_invalido_es_400(periodo: str, code: str) -> None:
    async with client() as c:
        response = await c.get(f"{SLA}/resumen", params={"periodo": periodo})

    assert response.status_code == 400
    assert response.json()["code"] == code


# --- GET /incidentes-vencidos ---------------------------------------------------


@pytest.mark.usefixtures("_sesion_view", "sla_gateway", "lookup")
async def test_incidentes_vencidos_filtra_a_los_pst_propios_por_default() -> None:
    async with client() as c:
        propios = await c.get(f"{SLA}/incidentes-vencidos", params={"periodo": PERIODO})
        todos = await c.get(
            f"{SLA}/incidentes-vencidos", params={"periodo": PERIODO, "todos": "true"}
        )
        ajeno = await c.get(
            f"{SLA}/incidentes-vencidos",
            params={"periodo": PERIODO, "operadorId": str(uuid.uuid4())},
        )

    assert propios.status_code == 200
    body = propios.json()
    assert set(body) == PAGE_KEYS
    assert body["total"] == 1
    assert set(body["items"][0]) == {
        "id_incidente", "tecnico", "id_tecnico", "region", "cliente", "sucursal", "modelo",
        "nro_serie", "fecha_ingreso", "fecha_operativo", "tiempo", "rango", "sla_horas",
        "horas_vencido",
    }
    assert body["items"][0]["id_incidente"] == 2
    assert [i["id_incidente"] for i in todos.json()["items"]] == [2, 3]
    # Otro operador sin PST: lista explícita vacía → no ve nada (no cae al "todo").
    assert ajeno.json()["total"] == 0


@pytest.mark.usefixtures("_sesion_view", "sla_gateway", "lookup")
async def test_incidentes_vencidos_size_fuera_de_rango_es_400() -> None:
    async with client() as c:
        response = await c.get(
            f"{SLA}/incidentes-vencidos", params={"periodo": PERIODO, "size": 501}
        )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


# --- POST /actualizar -----------------------------------------------------------


@pytest.mark.usefixtures("_sesion_update", "sla_gateway")
async def test_actualizar_consulta_en_vivo_y_devuelve_el_resumen(
    sla_gateway: FakeSlaQueryGateway,
) -> None:
    async with client() as c:
        response = await c.post(f"{SLA}/actualizar", params={"periodo": PERIODO})

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert [p.value for p in sla_gateway.periodos_consultados] == [PERIODO]
