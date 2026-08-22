"""`grilla_variantes_router` (modo vacaciones, ADR-025) por HTTP (ver
conftest.py de este paquete): 403 con solo `view` (el GET sin grant ya está en
test_require_permission_http.py), el ciclo crear → listar → editar → cancelar
con su contrato (envelope `Page[T]`, aliases camelCase), la precarga de solo
lectura y los 400/404 de las reglas de dominio más visibles."""

from __future__ import annotations

import uuid

import pytest

from tests.integration.router_testing import client
from tests.integration.turnos.support import (
    PAGE_KEYS,
    PREFIX,
    ReposCoberturas,
    variante_body,
    variante_slot_body,
)

_URL = f"{PREFIX}/grilla-variantes"


@pytest.mark.usefixtures("_sesion_view", "repos_coberturas")
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", _URL),
        ("PUT", f"{_URL}/{uuid.uuid4()}"),
        ("POST", f"{_URL}/{uuid.uuid4()}/cancelar"),
    ],
)
async def test_mutaciones_con_solo_view_devuelven_403(method: str, path: str) -> None:
    async with client() as c:
        response = await c.request(method, path, json={})

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.usefixtures("_sesion_solo_sesion", "repos_coberturas")
async def test_precarga_sin_grant_view_devuelve_403() -> None:
    async with client() as c:
        response = await c.post(f"{_URL}/precarga")

    assert response.status_code == 403


@pytest.mark.usefixtures("_sesion_manage")
async def test_crear_listar_editar_y_cancelar_grilla_variante(
    repos_coberturas: ReposCoberturas,
) -> None:
    repos = repos_coberturas
    async with client() as c:
        creada = await c.post(_URL, json=variante_body(repos))
        variante_id = creada.json()["id"]
        listado = await c.get(_URL)
        editada = await c.put(f"{_URL}/{variante_id}", json=variante_body(repos, motivo="Editada"))
        cancelada = await c.post(f"{_URL}/{variante_id}/cancelar")
        vigentes = await c.get(_URL, params={"vigentes": "true"})

    assert creada.status_code == 201
    body = creada.json()
    assert set(body) == {
        "id", "motivo", "origenTexto", "desde", "hasta", "estado", "createdByUserId", "slots",
        "advertencias",
    }
    assert body["estado"] == "ACTIVA"
    slot = body["slots"][0]
    assert set(slot) == {
        "id", "casillaId", "casillaNombre", "diaSemana", "horaInicio", "horaFin", "sortOrder",
        "operadores",
    }
    assert (slot["casillaNombre"], slot["horaInicio"], slot["horaFin"]) == (
        "INSUMOS", "08:00:00", "11:00:00"
    )
    assert slot["operadores"][0]["userName"] == "Luna Torres"
    # La titular del fake está vacía: no hay huecos contra los que advertir.
    assert body["advertencias"] == []
    assert listado.status_code == 200
    assert set(listado.json()) == PAGE_KEYS
    assert [v["id"] for v in listado.json()["items"]] == [variante_id]
    assert editada.status_code == 200
    assert editada.json()["motivo"] == "Editada"
    assert cancelada.status_code == 204
    assert repos.variantes.rows[uuid.UUID(variante_id)].estado == "CANCELADA"
    assert vigentes.json()["total"] == 0


@pytest.mark.usefixtures("_sesion_manage")
@pytest.mark.parametrize(
    ("extra", "code"),
    [
        ({"slots": []}, "VARIANTE_SIN_FRANJAS"),
        ({"desde": "2026-09-01"}, "INVALID_VARIANTE_RANGE"),
        ({"motivo": "x" * 201}, "VALIDATION_ERROR"),
        ({"hasta": None}, "VALIDATION_ERROR"),
    ],
)
async def test_crear_grilla_variante_invalida_es_400(
    repos_coberturas: ReposCoberturas, extra: dict[str, object], code: str
) -> None:
    async with client() as c:
        response = await c.post(_URL, json=variante_body(repos_coberturas, **extra))

    assert response.status_code == 400
    assert response.json()["code"] == code


@pytest.mark.usefixtures("_sesion_manage")
async def test_franja_con_casilla_inexistente_es_400(repos_coberturas: ReposCoberturas) -> None:
    slots = [variante_slot_body(repos_coberturas, casillaId=str(uuid.uuid4()))]
    async with client() as c:
        response = await c.post(_URL, json=variante_body(repos_coberturas, slots=slots))

    assert response.status_code == 400
    assert response.json()["code"] == "VARIANTE_CASILLA_INVALIDA"


@pytest.mark.usefixtures("_sesion_manage")
async def test_editar_o_cancelar_inexistente_es_404(repos_coberturas: ReposCoberturas) -> None:
    async with client() as c:
        editada = await c.put(f"{_URL}/{uuid.uuid4()}", json=variante_body(repos_coberturas))
        cancelada = await c.post(f"{_URL}/{uuid.uuid4()}/cancelar")

    assert editada.status_code == 404
    assert editada.json()["code"] == "GRILLA_VARIANTE_NOT_FOUND"
    assert cancelada.status_code == 404
    assert cancelada.json()["code"] == "GRILLA_VARIANTE_NOT_FOUND"


@pytest.mark.usefixtures("_sesion_view")
async def test_precarga_es_solo_lectura_y_devuelve_titular(
    repos_coberturas: ReposCoberturas,
) -> None:
    repos = repos_coberturas
    params = {"ausenteUserId": str(repos.majo), "desde": "2026-08-24", "hasta": "2026-08-28"}
    async with client() as c:
        response = await c.post(f"{_URL}/precarga", params=params)
        sin_params = await c.post(f"{_URL}/precarga")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "ausenteUserId", "ausenteNombre", "desde", "hasta", "slots", "advertencias"
    }
    assert (body["ausenteUserId"], body["ausenteNombre"]) == (str(repos.majo), "Maria Jose Vela")
    assert (body["desde"], body["hasta"]) == ("2026-08-24", "2026-08-28")
    assert body["slots"] == []  # titular vacía en el fake
    assert repos.variantes.rows == {}  # no persiste nada
    assert sin_params.status_code == 400
    assert sin_params.json()["code"] == "VALIDATION_ERROR"
