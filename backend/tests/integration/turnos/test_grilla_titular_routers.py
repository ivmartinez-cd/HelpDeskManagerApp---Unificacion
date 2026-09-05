"""Routers de la grilla titular (`turnos_router`, `casillas_router`,
`slots_router`) por HTTP (ver conftest.py de este paquete). Extiende
test_turnos_router.py (401) y test_require_permission_http.py (403 de algunos
endpoints): acá van los 403 restantes (view vs manage), un camino feliz por
endpoint con su contrato (envelope `Page[T]`, aliases camelCase) y los 400 de
validación del body."""

from __future__ import annotations

import uuid

import pytest

from tests.integration.router_testing import client
from tests.integration.turnos.support import PAGE_KEYS, PREFIX, ReposTitular

# --- Autorización (complementa test_require_permission_http.py) ----------------


@pytest.mark.usefixtures("_sesion_view", "repos_titular")
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", f"{PREFIX}/casillas"),
        ("PUT", f"{PREFIX}/casillas/{uuid.uuid4()}"),
        ("DELETE", f"{PREFIX}/casillas/{uuid.uuid4()}"),
        ("POST", f"{PREFIX}/slots"),
        ("PUT", f"{PREFIX}/slots/{uuid.uuid4()}"),
        ("DELETE", f"{PREFIX}/slots/{uuid.uuid4()}"),
        ("POST", f"{PREFIX}/slots/{uuid.uuid4()}/asignaciones"),
    ],
)
async def test_mutaciones_con_solo_view_devuelven_403(method: str, path: str) -> None:
    async with client() as c:
        response = await c.request(method, path, json={})

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.usefixtures("_sesion_solo_sesion", "repos_titular")
@pytest.mark.parametrize("path", [f"{PREFIX}/users", f"{PREFIX}/slots"])
async def test_consultas_sin_grant_view_devuelven_403(path: str) -> None:
    async with client() as c:
        response = await c.get(path)

    assert response.status_code == 403


# --- turnos_router: /current y /users -----------------------------------------


@pytest.mark.usefixtures("_sesion_solo_sesion")
async def test_current_es_solo_sesion_y_devuelve_page_mas_variante(
    repos_titular: ReposTitular,
) -> None:
    async with client() as c:
        response = await c.get(f"{PREFIX}/current")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == PAGE_KEYS | {"varianteActiva"}
    assert body["varianteActiva"] is None
    assert body["total"] == 1
    shift = body["items"][0]
    assert set(shift) == {
        "slotId",
        "casillaId",
        "casillaNombre",
        "casillaColor",
        "horaInicio",
        "horaFin",
        "diaSemana",
        "operadores",
        "isCurrent",
        "isNext",
    }
    assert shift["slotId"] == str(repos_titular.slot.id)
    assert shift["casillaNombre"] == "INSUMOS"
    assert shift["isCurrent"] is True
    assert shift["operadores"] == [
        {
            "userId": str(repos_titular.luna),
            "userName": "Luna Torres",
            "color": "#123456",
            "nota": None,
        }
    ]


@pytest.mark.usefixtures("_sesion_view")
async def test_users_lista_activos_paginado(repos_titular: ReposTitular) -> None:
    async with client() as c:
        response = await c.get(f"{PREFIX}/users", params={"size": 5})

    assert response.status_code == 200
    body = response.json()
    assert set(body) == PAGE_KEYS
    assert (body["total"], body["size"]) == (1, 5)
    assert body["items"] == [
        {"id": str(repos_titular.luna), "fullName": "Luna Torres", "color": "#123456"}
    ]


# --- casillas_router ------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view")
async def test_listar_casillas_paginado(repos_titular: ReposTitular) -> None:
    async with client() as c:
        response = await c.get(f"{PREFIX}/casillas")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == PAGE_KEYS
    assert body["items"] == [
        {
            "id": str(repos_titular.casilla.id),
            "nombre": "INSUMOS",
            "color": "#F7941D",
            "sortOrder": 0,
            "isActive": True,
        }
    ]


@pytest.mark.usefixtures("_sesion_manage")
async def test_crear_editar_y_borrar_casilla(repos_titular: ReposTitular) -> None:
    async with client() as c:
        creada = await c.post(
            f"{PREFIX}/casillas", json={"nombre": "ST", "color": "#58595B", "sortOrder": 1}
        )
        casilla_id = creada.json()["id"]
        editada = await c.put(f"{PREFIX}/casillas/{casilla_id}", json={"nombre": "SOPORTE"})
        borrada = await c.delete(f"{PREFIX}/casillas/{casilla_id}")

    assert creada.status_code == 201
    assert creada.json() == {
        "id": casilla_id,
        "nombre": "ST",
        "color": "#58595B",
        "sortOrder": 1,
        "isActive": True,
    }
    assert editada.status_code == 200
    # Solo `nombre` es editable: color/orden se preservan aunque el body no los traiga.
    assert (editada.json()["nombre"], editada.json()["color"]) == ("SOPORTE", "#58595B")

    assert borrada.status_code == 204
    assert uuid.UUID(casilla_id) not in repos_titular.casillas.rows


@pytest.mark.usefixtures("_sesion_manage", "repos_titular")
async def test_editar_casilla_inexistente_es_404() -> None:
    """Antes el use case lanzaba `ValueError` sin mapear (terminaba en 500)."""
    async with client() as c:
        response = await c.put(f"{PREFIX}/casillas/{uuid.uuid4()}", json={"nombre": "X"})

    assert response.status_code == 404
    assert response.json()["code"] == "CASILLA_NOT_FOUND"


@pytest.mark.usefixtures("_sesion_manage", "repos_titular")
async def test_crear_casilla_sin_nombre_es_400() -> None:
    async with client() as c:
        response = await c.post(f"{PREFIX}/casillas", json={"color": "#000"})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


# --- slots_router ---------------------------------------------------------------


@pytest.mark.usefixtures("_sesion_view")
async def test_listar_slots_filtra_por_casilla_y_resuelve_nombres(
    repos_titular: ReposTitular,
) -> None:
    async with client() as c:
        propios = await c.get(
            f"{PREFIX}/slots", params={"casilla_id": str(repos_titular.casilla.id)}
        )
        otra = await c.get(f"{PREFIX}/slots", params={"casilla_id": str(uuid.uuid4())})

    assert propios.status_code == 200
    body = propios.json()
    assert set(body) == PAGE_KEYS
    assert body["total"] == 1
    slot = body["items"][0]
    assert set(slot) == {
        "id",
        "casillaId",
        "horaInicio",
        "horaFin",
        "diaSemana",
        "sortOrder",
        "asignaciones",
    }
    assert slot["asignaciones"][0]["userName"] == "Luna Torres"
    assert otra.json()["total"] == 0


@pytest.mark.usefixtures("_sesion_manage")
async def test_crear_editar_borrar_slot_y_reasignar(repos_titular: ReposTitular) -> None:
    body = {
        "casillaId": str(repos_titular.casilla.id),
        "horaInicio": "08:00",
        "horaFin": "11:00",
        "diaSemana": 2,
        "sortOrder": 3,
    }
    # Un usuario que existe en el provider: los ids desconocidos ahora dan 404.
    nuevo = repos_titular.luna
    async with client() as c:
        creado = await c.post(f"{PREFIX}/slots", json=body)
        slot_id = creado.json()["id"]
        editado = await c.put(f"{PREFIX}/slots/{slot_id}", json={**body, "horaFin": "12:00"})
        reasignado = await c.post(
            f"{PREFIX}/slots/{slot_id}/asignaciones",
            json={"userIds": [str(nuevo)], "vigenteDesde": "2026-09-01"},
        )
        borrado = await c.delete(f"{PREFIX}/slots/{slot_id}")

    assert creado.status_code == 201
    assert creado.json() == {
        "id": slot_id,
        "casillaId": str(repos_titular.casilla.id),
        "horaInicio": "08:00:00",
        "horaFin": "11:00:00",
        "diaSemana": 2,
        "sortOrder": 3,
        "asignaciones": [],
    }
    assert editado.status_code == 200
    assert (editado.json()["horaFin"], editado.json()["sortOrder"]) == ("12:00:00", 3)
    assert reasignado.status_code == 204
    assert borrado.status_code == 204
    assert uuid.UUID(slot_id) not in repos_titular.slots.rows
    asignaciones = repos_titular.asignaciones.rows.values()
    assert [a for a in asignaciones if a.slot_id == uuid.UUID(slot_id)] == []


@pytest.mark.usefixtures("_sesion_manage", "repos_titular")
@pytest.mark.parametrize(
    "body",
    [
        {},
        {"casillaId": "no-es-uuid", "horaInicio": "08:00", "horaFin": "11:00", "diaSemana": 0},
        {"casillaId": str(uuid.uuid4()), "horaInicio": "25:00", "horaFin": "11:00", "diaSemana": 0},
    ],
)
async def test_crear_slot_con_body_invalido_es_400(body: dict[str, object]) -> None:
    async with client() as c:
        response = await c.post(f"{PREFIX}/slots", json=body)

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
