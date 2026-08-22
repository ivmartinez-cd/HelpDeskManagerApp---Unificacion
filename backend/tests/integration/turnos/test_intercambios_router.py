"""`intercambios_router` (ADR-026) por HTTP (ver conftest.py de este paquete):
403 con solo `view` (el POST sin grant ya está en
test_require_permission_http.py), el ciclo crear → editar → cancelar con el
contrato del par de coberturas cruzadas, el 404 y el 400 de body."""

from __future__ import annotations

import uuid

import pytest

from tests.integration.router_testing import client
from tests.integration.turnos.support import OVERRIDE_KEYS, PREFIX, ReposCoberturas

_URL = f"{PREFIX}/intercambios"


def _body(repos: ReposCoberturas, **extra: object) -> dict[str, object]:
    return {
        "operadorAId": str(repos.majo),
        "operadorBId": str(repos.luna),
        "desde": "2026-08-20",
        "hasta": "2026-08-20",
        **extra,
    }


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


@pytest.mark.usefixtures("_sesion_manage")
async def test_crear_editar_y_cancelar_intercambio(repos_coberturas: ReposCoberturas) -> None:
    repos = repos_coberturas
    async with client() as c:
        creado = await c.post(_URL, json=_body(repos))
        intercambio_id = creado.json()["intercambioId"]
        editado = await c.put(f"{_URL}/{intercambio_id}", json=_body(repos, motivo="cambio"))
        cancelado = await c.post(f"{_URL}/{intercambio_id}/cancelar")

    assert creado.status_code == 201
    assert set(creado.json()) == {"intercambioId", "coberturas"}
    coberturas = creado.json()["coberturas"]
    assert len(coberturas) == 2
    assert all(set(cob) == OVERRIDE_KEYS for cob in coberturas)
    assert {cob["intercambioId"] for cob in coberturas} == {intercambio_id}
    assert [(cob["operadorAusenteId"], cob["operadorReemplazanteId"]) for cob in coberturas] == [
        (str(repos.majo), str(repos.luna)), (str(repos.luna), str(repos.majo))
    ]
    assert all(cob["motivo"] == "Intercambio" for cob in coberturas)
    assert editado.status_code == 200
    assert all(cob["motivo"] == "cambio" for cob in editado.json()["coberturas"])
    assert cancelado.status_code == 204
    assert {o.estado for o in repos.overrides.rows.values()} == {"CANCELADA"}


@pytest.mark.usefixtures("_sesion_manage")
async def test_alcance_parcial_por_lado(repos_coberturas: ReposCoberturas) -> None:
    franja_a = str(uuid.uuid4())
    async with client() as c:
        response = await c.post(_URL, json=_body(repos_coberturas, slotIdsA=[franja_a]))

    assert response.status_code == 201
    ida, vuelta = response.json()["coberturas"]
    assert (ida["alcanceTotal"], ida["slotIds"]) == (False, [franja_a])
    assert (vuelta["alcanceTotal"], vuelta["slotIds"]) == (True, [])


@pytest.mark.usefixtures("_sesion_manage", "repos_coberturas")
async def test_editar_o_cancelar_inexistente_es_404(repos_coberturas: ReposCoberturas) -> None:
    async with client() as c:
        editado = await c.put(f"{_URL}/{uuid.uuid4()}", json=_body(repos_coberturas))
        cancelado = await c.post(f"{_URL}/{uuid.uuid4()}/cancelar")

    assert editado.status_code == 404
    assert editado.json()["code"] == "INTERCAMBIO_NOT_FOUND"
    assert cancelado.status_code == 404
    assert cancelado.json()["code"] == "INTERCAMBIO_NOT_FOUND"


@pytest.mark.usefixtures("_sesion_manage", "repos_coberturas")
async def test_crear_intercambio_sin_operadores_es_400() -> None:
    async with client() as c:
        response = await c.post(_URL, json={"desde": "2026-08-20", "hasta": "2026-08-20"})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.usefixtures("_sesion_manage")
async def test_crear_intercambio_con_rango_invertido_es_400(
    repos_coberturas: ReposCoberturas,
) -> None:
    async with client() as c:
        response = await c.post(_URL, json=_body(repos_coberturas, desde="2026-08-21"))

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_OVERRIDE_RANGE"
