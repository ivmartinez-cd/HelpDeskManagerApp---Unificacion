"""Dar acceso crea la cuenta desde la ficha (o reactiva la que había); quitarlo
la desactiva sin desvincular."""

import uuid

import pytest

from src.modules.personas.application.use_cases.gestionar_acceso import (
    AccesoDependencies,
    DarAcceso,
    QuitarAcceso,
)
from src.modules.personas.domain.errors import (
    CuentaPrivilegiadaError,
    EmailEnUsoError,
    PersonaInactivaError,
)
from tests.unit.application.personas.fakes import (
    FakeAviso,
    FakeCuentas,
    FakeFichas,
    FakePersonaRepository,
    Mundo,
    make_acceso,
    make_persona,
)


def _dar(mundo: Mundo) -> DarAcceso:
    return DarAcceso(
        AccesoDependencies(
            personas=FakePersonaRepository(mundo),
            fichas=FakeFichas(mundo),
            cuentas=FakeCuentas(mundo),
            aviso=FakeAviso(mundo),
        )
    )


def _quitar(mundo: Mundo) -> QuitarAcceso:
    return QuitarAcceso(FakePersonaRepository(mundo), FakeCuentas(mundo))


async def test_sin_cuenta_la_crea_vincula_y_manda_activacion() -> None:
    persona = make_persona()
    mundo = Mundo(persona)

    resultado = await _dar(mundo).execute(persona.id, actor_es_superadmin=False)

    assert resultado.entra_a_la_app
    assert resultado.acceso is not None
    assert mundo.cuentas[resultado.acceso.user_id][0] == "ana@canal.com"
    assert mundo.mails == ["ana@canal.com"]


async def test_con_cuenta_desactivada_la_reactiva_sin_mail() -> None:
    persona = make_persona(acceso=make_acceso(activo=False))
    mundo = Mundo(persona)

    resultado = await _dar(mundo).execute(persona.id, actor_es_superadmin=False)

    assert resultado.entra_a_la_app
    assert mundo.mails == []


async def test_con_acceso_activo_no_hace_nada() -> None:
    persona = make_persona(acceso=make_acceso())
    mundo = Mundo(persona)

    resultado = await _dar(mundo).execute(persona.id, actor_es_superadmin=False)

    assert resultado == persona
    assert mundo.mails == []


async def test_persona_inactiva_no_recibe_acceso() -> None:
    persona = make_persona(activa=False)

    with pytest.raises(PersonaInactivaError):
        await _dar(Mundo(persona)).execute(persona.id, actor_es_superadmin=False)


async def test_mail_tomado_por_otra_cuenta_es_conflicto() -> None:
    persona = make_persona()
    mundo = Mundo(persona)
    mundo.cuentas[uuid.uuid4()] = ("ana@canal.com", False, None)

    with pytest.raises(EmailEnUsoError):
        await _dar(mundo).execute(persona.id, actor_es_superadmin=False)
    assert mundo.mails == []


async def test_quitar_acceso_desactiva_y_conserva_el_vinculo() -> None:
    persona = make_persona(acceso=make_acceso())
    mundo = Mundo(persona)

    resultado = await _quitar(mundo).execute(persona.id, actor_es_superadmin=False)

    assert resultado.acceso is not None and not resultado.acceso.activo
    assert not resultado.entra_a_la_app


async def test_quitar_acceso_sin_cuenta_es_idempotente() -> None:
    persona = make_persona()

    resultado = await _quitar(Mundo(persona)).execute(persona.id, actor_es_superadmin=False)

    assert resultado.acceso is None


def _con_admin(*, activo: bool) -> tuple[Mundo, uuid.UUID]:
    persona = make_persona(acceso=make_acceso(activo=activo))
    mundo = Mundo(persona)
    assert persona.acceso is not None
    mundo.privilegiadas.add(persona.acceso.user_id)
    return mundo, persona.id


async def test_quitar_acceso_a_un_admin_exige_superadmin() -> None:
    mundo, persona_id = _con_admin(activo=True)

    with pytest.raises(CuentaPrivilegiadaError):
        await _quitar(mundo).execute(persona_id, actor_es_superadmin=False)

    resultado = await _quitar(mundo).execute(persona_id, actor_es_superadmin=True)
    assert not resultado.entra_a_la_app


async def test_reactivar_a_un_admin_exige_superadmin() -> None:
    mundo, persona_id = _con_admin(activo=False)

    with pytest.raises(CuentaPrivilegiadaError):
        await _dar(mundo).execute(persona_id, actor_es_superadmin=False)

    resultado = await _dar(mundo).execute(persona_id, actor_es_superadmin=True)
    assert resultado.entra_a_la_app
