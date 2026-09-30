"""`/api/personas` por HTTP (ADR-040): permisos propios por endpoint, envelope
Page, y cambio de mail de quien entra a la app solo con `personas.manage`."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest

import src.modules.personas.presentation.dependencies as armado
from src.modules.personas.application.use_cases.actualizar_datos_persona import (
    ActualizarDatosDependencies,
)
from src.modules.personas.application.use_cases.gestionar_acceso import AccesoDependencies
from src.modules.personas.domain.entities.persona import Persona
from tests.integration.router_testing import client, install_session, uninstall_session
from tests.unit.application.personas.fakes import (
    FakeAviso,
    FakeCuentas,
    FakeFichas,
    FakePersonaRepository,
    Mundo,
    make_acceso,
    make_persona,
)

URL = "/api/personas"
_VER = ("personas", "view")
_EDITAR = ("personas", "update")
_GESTIONAR = ("personas", "manage")


@pytest.fixture
def persona(monkeypatch: pytest.MonkeyPatch) -> Iterator[Persona]:
    persona = make_persona(acceso=make_acceso())
    mundo = Mundo(persona)
    monkeypatch.setattr(armado, "repositorio", lambda _db: FakePersonaRepository(mundo))
    monkeypatch.setattr(armado, "cuentas", lambda _db: FakeCuentas(mundo))
    monkeypatch.setattr(
        armado,
        "deps_datos",
        lambda _db, _actor: ActualizarDatosDependencies(
            personas=FakePersonaRepository(mundo),
            fichas=FakeFichas(mundo),
            cuentas=FakeCuentas(mundo),
        ),
    )
    monkeypatch.setattr(
        armado,
        "deps_acceso",
        lambda _db, _actor, _bg: AccesoDependencies(
            personas=FakePersonaRepository(mundo),
            fichas=FakeFichas(mundo),
            cuentas=FakeCuentas(mundo),
            aviso=FakeAviso(mundo),
        ),
    )
    yield persona
    uninstall_session()


def _datos(email: str) -> dict[str, str]:
    return {"firstName": "Ana", "lastName": "Paz", "email": email, "color": "#112233"}


async def test_sin_sesion_es_401(persona: Persona) -> None:
    async with client() as c:
        assert (await c.get(URL)).status_code == 401


async def test_sin_permiso_de_personas_es_403(
    persona: Persona, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_session(monkeypatch, ("vacaciones", "manage"))
    async with client() as c:
        assert (await c.get(URL)).status_code == 403


async def test_listado_paginado_en_camel_case(
    persona: Persona, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_session(monkeypatch, _VER)
    async with client() as c:
        response = await c.get(URL, params={"sortBy": "acceso", "sortDir": "desc"})

    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 1 and body["page"] == 1
    item = body["items"][0]
    assert item["id"] == str(persona.id) and item["entraALaApp"] is True
    assert item["acceso"]["activo"] is True


async def test_ficha_inexistente_es_404(persona: Persona, monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch, _VER)
    async with client() as c:
        assert (await c.get(f"{URL}/{uuid.uuid4()}")).status_code == 404


async def test_cambiar_mail_de_quien_entra_sin_gestionar_es_403(
    persona: Persona, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_session(monkeypatch, _VER, _EDITAR)
    async with client() as c:
        cambio = await c.patch(f"{URL}/{persona.id}/datos", json=_datos("otra@canal.com"))
        mismo = await c.patch(f"{URL}/{persona.id}/datos", json=_datos("ana@canal.com"))

    assert cambio.status_code == 403
    assert mismo.status_code == 200


async def test_cambiar_mail_con_gestionar_es_200(
    persona: Persona, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_session(monkeypatch, _EDITAR, _GESTIONAR)
    async with client() as c:
        response = await c.patch(f"{URL}/{persona.id}/datos", json=_datos("Otra@Canal.com"))

    assert response.status_code == 200
    assert response.json()["email"] == "otra@canal.com"


async def test_datos_invalidos_son_400(persona: Persona, monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch, _EDITAR)
    body = {**_datos("ana@canal.com"), "color": "rojo"}
    async with client() as c:
        assert (await c.patch(f"{URL}/{persona.id}/datos", json=body)).status_code == 400


async def test_acceso_exige_gestionar(persona: Persona, monkeypatch: pytest.MonkeyPatch) -> None:
    install_session(monkeypatch, _VER, _EDITAR)
    async with client() as c:
        assert (await c.delete(f"{URL}/{persona.id}/acceso")).status_code == 403


async def test_quitar_y_volver_a_dar_acceso(
    persona: Persona, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_session(monkeypatch, _GESTIONAR)
    async with client() as c:
        quitado = await c.delete(f"{URL}/{persona.id}/acceso")
        dado = await c.post(f"{URL}/{persona.id}/acceso")

    assert quitado.status_code == 200 and quitado.json()["entraALaApp"] is False
    assert dado.status_code == 200 and dado.json()["entraALaApp"] is True


async def test_mail_y_acceso_de_un_admin_solo_los_toca_un_superadmin(
    persona: Persona, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _privilegiada(_self: FakeCuentas, _user_id: uuid.UUID) -> bool:
        return True

    monkeypatch.setattr(FakeCuentas, "es_privilegiada", _privilegiada)
    install_session(monkeypatch, _EDITAR, _GESTIONAR)
    async with client() as c:
        mail = await c.patch(f"{URL}/{persona.id}/datos", json=_datos("yo@canal.com"))
        quitado = await c.delete(f"{URL}/{persona.id}/acceso")

    assert mail.status_code == 403
    assert mail.json()["code"] == "PERSONA_CUENTA_PRIVILEGIADA"
    assert quitado.status_code == 403
