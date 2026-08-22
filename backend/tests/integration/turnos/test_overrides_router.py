"""`overrides_router` (coberturas ADR-013) por HTTP (ver conftest.py de este
paquete): 403 con solo `view`, el ciclo crear → listar → editar → cancelar con
su contrato (aliases camelCase), el alcance por franja y los 400/404/409 de
las reglas de dominio más visibles."""

from __future__ import annotations

import uuid

import pytest

from tests.integration.router_testing import client
from tests.integration.turnos.support import (
    OVERRIDE_KEYS,
    PAGE_KEYS,
    PREFIX,
    ReposCoberturas,
    override_body,
)


@pytest.mark.usefixtures("_sesion_view", "repos_coberturas")
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", f"{PREFIX}/overrides"),
        ("PUT", f"{PREFIX}/overrides/{uuid.uuid4()}"),
        ("POST", f"{PREFIX}/overrides/{uuid.uuid4()}/cancelar"),
    ],
)
async def test_mutaciones_con_solo_view_devuelven_403(method: str, path: str) -> None:
    async with client() as c:
        response = await c.request(method, path, json={})

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.usefixtures("_sesion_solo_sesion", "repos_coberturas")
async def test_listar_sin_grant_view_devuelve_403() -> None:
    async with client() as c:
        response = await c.get(f"{PREFIX}/overrides")

    assert response.status_code == 403


@pytest.mark.usefixtures("_sesion_manage")
async def test_crear_listar_editar_y_cancelar_cobertura(repos_coberturas: ReposCoberturas) -> None:
    repos = repos_coberturas
    async with client() as c:
        creada = await c.post(f"{PREFIX}/overrides", json=override_body(repos))
        override_id = creada.json()["id"]
        listado = await c.get(f"{PREFIX}/overrides")
        editada = await c.put(
            f"{PREFIX}/overrides/{override_id}",
            json=override_body(repos, hasta="2026-08-31", motivo="extendida"),
        )
        cancelada = await c.post(f"{PREFIX}/overrides/{override_id}/cancelar")

    assert creada.status_code == 201
    body = creada.json()
    assert set(body) == OVERRIDE_KEYS
    assert (body["operadorAusenteNombre"], body["operadorReemplazanteNombre"]) == (
        "Maria Jose Vela", "Luna Torres"
    )
    assert (body["alcanceTotal"], body["slotIds"], body["estado"]) == (True, [], "ACTIVA")
    assert body["intercambioId"] is None
    assert listado.status_code == 200
    assert set(listado.json()) == PAGE_KEYS
    assert [o["id"] for o in listado.json()["items"]] == [override_id]
    assert editada.status_code == 200
    assert (editada.json()["hasta"], editada.json()["motivo"]) == ("2026-08-31", "extendida")
    assert cancelada.status_code == 204
    assert repos.overrides.rows[uuid.UUID(override_id)].estado == "CANCELADA"


@pytest.mark.usefixtures("_sesion_manage")
async def test_crear_cobertura_con_alcance_por_franja(repos_coberturas: ReposCoberturas) -> None:
    franja = str(uuid.uuid4())
    async with client() as c:
        response = await c.post(
            f"{PREFIX}/overrides", json=override_body(repos_coberturas, slotIds=[franja])
        )

    assert response.status_code == 201
    assert (response.json()["alcanceTotal"], response.json()["slotIds"]) == (False, [franja])


@pytest.mark.usefixtures("_sesion_manage")
@pytest.mark.parametrize(
    ("extra", "code"),
    [
        ({"desde": "2026-09-01"}, "INVALID_OVERRIDE_RANGE"),
        ({"desde": "ayer"}, "VALIDATION_ERROR"),
        ({"operadorAusenteId": None}, "VALIDATION_ERROR"),
    ],
)
async def test_crear_cobertura_invalida_es_400(
    repos_coberturas: ReposCoberturas, extra: dict[str, object], code: str
) -> None:
    async with client() as c:
        response = await c.post(
            f"{PREFIX}/overrides", json=override_body(repos_coberturas, **extra)
        )

    assert response.status_code == 400
    assert response.json()["code"] == code


@pytest.mark.usefixtures("_sesion_manage")
async def test_mismo_operador_ausente_y_reemplazante_es_400(
    repos_coberturas: ReposCoberturas,
) -> None:
    body = override_body(repos_coberturas, operadorReemplazanteId=str(repos_coberturas.majo))
    async with client() as c:
        response = await c.post(f"{PREFIX}/overrides", json=body)

    assert response.status_code == 400
    assert response.json()["code"] == "OVERRIDE_MISMO_OPERADOR"


@pytest.mark.usefixtures("_sesion_manage")
async def test_cobertura_solapada_es_409_y_cancelar_inexistente_404(
    repos_coberturas: ReposCoberturas,
) -> None:
    async with client() as c:
        await c.post(f"{PREFIX}/overrides", json=override_body(repos_coberturas))
        solapada = await c.post(f"{PREFIX}/overrides", json=override_body(repos_coberturas))
        inexistente = await c.post(f"{PREFIX}/overrides/{uuid.uuid4()}/cancelar")

    assert solapada.status_code == 409
    assert solapada.json()["code"] == "OVERLAPPING_OVERRIDE"
    assert inexistente.status_code == 404
    assert inexistente.json()["code"] == "ASIGNACION_OVERRIDE_NOT_FOUND"
