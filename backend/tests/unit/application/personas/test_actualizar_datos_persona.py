"""Editar nombre/mail/color escribe en la ficha y en la cuenta, y protege el
cambio de mail de quien entra a la app."""

import uuid

import pytest

from src.modules.personas.application.use_cases.actualizar_datos_persona import (
    ActorPersonas,
    ActualizarDatosDependencies,
    ActualizarDatosPersona,
)
from src.modules.personas.domain.entities.persona import DatosPersona, Persona
from src.modules.personas.domain.errors import (
    CambioDeMailNoPermitidoError,
    CuentaPrivilegiadaError,
    EmailEnUsoError,
    PersonaNoEncontradaError,
)
from tests.unit.application.personas.fakes import (
    FakeCuentas,
    FakeFichas,
    FakePersonaRepository,
    Mundo,
    make_acceso,
    make_persona,
)


def _caso(mundo: Mundo) -> ActualizarDatosPersona:
    return ActualizarDatosPersona(
        ActualizarDatosDependencies(
            personas=FakePersonaRepository(mundo),
            fichas=FakeFichas(mundo),
            cuentas=FakeCuentas(mundo),
        )
    )


def _datos(email: str = "ana@canal.com", color: str = "#445566") -> DatosPersona:
    return DatosPersona(first_name="Ana María", last_name="Paz", email=email, color=color)


async def _ejecutar(
    mundo: Mundo, persona: Persona, datos: DatosPersona, *, gestiona: bool, superadmin: bool = False
) -> Persona:
    actor = ActorPersonas(puede_gestionar_acceso=gestiona, es_superadmin=superadmin)
    return await _caso(mundo).execute(persona.id, datos, actor=actor)


async def test_con_cuenta_escribe_en_ficha_y_cuenta() -> None:
    persona = make_persona(acceso=make_acceso())
    mundo = Mundo(persona)

    resultado = await _ejecutar(mundo, persona, _datos(), gestiona=False)

    assert resultado.datos == _datos()
    assert persona.acceso is not None
    assert mundo.cuentas[persona.acceso.user_id][2] == _datos()


async def test_sin_cuenta_solo_escribe_la_ficha() -> None:
    persona = make_persona()
    mundo = Mundo(persona)

    resultado = await _ejecutar(mundo, persona, _datos(email="nueva@canal.com"), gestiona=False)

    assert resultado.datos.email == "nueva@canal.com"
    assert mundo.cuentas == {}


async def test_cambiar_mail_de_quien_entra_exige_gestionar_acceso() -> None:
    persona = make_persona(acceso=make_acceso())
    mundo = Mundo(persona)

    with pytest.raises(CambioDeMailNoPermitidoError):
        await _ejecutar(mundo, persona, _datos(email="otra@canal.com"), gestiona=False)

    resultado = await _ejecutar(mundo, persona, _datos(email="otra@canal.com"), gestiona=True)
    assert resultado.datos.email == "otra@canal.com"


async def test_mail_de_otra_ficha_es_conflicto() -> None:
    persona, otra = make_persona(), make_persona(email="otra@canal.com")
    mundo = Mundo(persona, otra)

    with pytest.raises(EmailEnUsoError):
        await _ejecutar(mundo, persona, _datos(email="otra@canal.com"), gestiona=True)


async def test_mail_de_una_cuenta_ajena_es_conflicto() -> None:
    persona = make_persona()
    mundo = Mundo(persona)
    mundo.cuentas[uuid.uuid4()] = ("ajena@canal.com", False, None)

    with pytest.raises(EmailEnUsoError):
        await _ejecutar(mundo, persona, _datos(email="ajena@canal.com"), gestiona=True)


async def test_persona_inexistente() -> None:
    with pytest.raises(PersonaNoEncontradaError):
        await _caso(Mundo()).execute(
            uuid.uuid4(),
            _datos(),
            actor=ActorPersonas(puede_gestionar_acceso=True, es_superadmin=True),
        )


async def test_cambiar_mail_de_un_admin_exige_superadmin() -> None:
    persona = make_persona(acceso=make_acceso())
    mundo = Mundo(persona)
    assert persona.acceso is not None
    mundo.privilegiadas.add(persona.acceso.user_id)

    with pytest.raises(CuentaPrivilegiadaError):
        await _ejecutar(mundo, persona, _datos(email="atacante@canal.com"), gestiona=True)
    assert mundo.cuentas[persona.acceso.user_id][0] == "ana@canal.com"

    await _ejecutar(mundo, persona, _datos(email="nuevo@canal.com"), gestiona=True, superadmin=True)
    assert mundo.cuentas[persona.acceso.user_id][0] == "nuevo@canal.com"


async def test_editar_nombre_de_un_admin_sin_tocar_el_mail_no_exige_superadmin() -> None:
    persona = make_persona(acceso=make_acceso())
    mundo = Mundo(persona)
    assert persona.acceso is not None
    mundo.privilegiadas.add(persona.acceso.user_id)

    resultado = await _ejecutar(mundo, persona, _datos(), gestiona=False)

    assert resultado.datos.first_name == "Ana María"
