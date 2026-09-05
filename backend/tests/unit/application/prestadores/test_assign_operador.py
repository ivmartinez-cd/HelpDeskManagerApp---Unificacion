import uuid
from datetime import date, timedelta

import pytest

from src.modules.prestadores.application.dtos.prestador_dtos import AssignOperadorCommand
from src.modules.prestadores.application.use_cases.assign_operador import (
    AssignOperador,
    AssignOperadorDependencies,
)
from src.modules.prestadores.domain.entities.asignacion_historial import AsignacionHistorial
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.errors import OperadorNoEncontradoError
from src.modules.prestadores.domain.repositories.user_provider import UserInfo
from tests.unit.domain.prestadores.fakes import (
    FakeAsignacionHistorialRepository,
    FakeContactoRepository,
    FakePrestadorRepository,
    FakeUserProvider,
)

_HOY = date.today()


def _deps(
    prestadores: FakePrestadorRepository,
    asignaciones: FakeAsignacionHistorialRepository,
    *operadores: uuid.UUID,
) -> AssignOperadorDependencies:
    users = FakeUserProvider()
    for operador_id in operadores:
        users.users[operador_id] = UserInfo(id=operador_id, full_name=f"Operador {operador_id}")
    return AssignOperadorDependencies(
        prestadores=prestadores,
        asignaciones=asignaciones,
        contactos=FakeContactoRepository(),
        users=users,
    )


def _prestador(operador_id: uuid.UUID | None) -> Prestador:
    return Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=1,
        den_comercial="PST Rosario",
        razon_social=None,
        cuit=None,
        equipos=None,
        operador_id=operador_id,
        is_active=True,
    )


def _tramo_abierto(
    asignaciones: FakeAsignacionHistorialRepository,
    prestador: Prestador,
    operador_id: uuid.UUID | None,
    desde: date,
) -> AsignacionHistorial:
    tramo = AsignacionHistorial(
        id=uuid.uuid4(), prestador_id=prestador.id, operador_id=operador_id, desde=desde, hasta=None
    )
    asignaciones.rows[tramo.id] = tramo
    return tramo


def _tramos_ordenados(
    asignaciones: FakeAsignacionHistorialRepository,
) -> list[tuple[uuid.UUID | None, date, date | None]]:
    return sorted(
        ((t.operador_id, t.desde, t.hasta) for t in asignaciones.rows.values()),
        key=lambda t: t[1],
    )


async def test_reasignar_actualiza_el_puntero_y_cierra_el_tramo_anterior() -> None:
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()
    operador_viejo, operador_nuevo = uuid.uuid4(), uuid.uuid4()
    prestador = _prestador(operador_viejo)
    prestadores.rows[prestador.id] = prestador
    _tramo_abierto(asignaciones, prestador, operador_viejo, date(2025, 9, 4))
    desde = _HOY - timedelta(days=3)

    use_case = AssignOperador(_deps(prestadores, asignaciones, operador_viejo, operador_nuevo))
    dto = await use_case.execute(
        AssignOperadorCommand(prestador_id=prestador.id, operador_id=operador_nuevo, desde=desde)
    )

    assert dto.operador_id == operador_nuevo
    assert prestadores.rows[prestador.id].operador_id == operador_nuevo
    assert _tramos_ordenados(asignaciones) == [
        (operador_viejo, date(2025, 9, 4), desde - timedelta(days=1)),
        (operador_nuevo, desde, None),
    ]


async def test_desasignar_deja_operador_id_en_none() -> None:
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()
    operador = uuid.uuid4()
    prestador = _prestador(operador)
    prestadores.rows[prestador.id] = prestador

    use_case = AssignOperador(_deps(prestadores, asignaciones, operador))
    dto = await use_case.execute(
        AssignOperadorCommand(prestador_id=prestador.id, operador_id=None, desde=_HOY)
    )

    assert dto.operador_id is None
    assert prestadores.rows[prestador.id].operador_id is None


async def test_asignar_a_futuro_no_mueve_el_puntero_pero_programa_el_tramo() -> None:
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()
    opa, opb = uuid.uuid4(), uuid.uuid4()
    prestador = _prestador(opa)
    prestadores.rows[prestador.id] = prestador
    _tramo_abierto(asignaciones, prestador, opa, date(2025, 1, 1))
    futuro = _HOY + timedelta(days=30)

    dto = await AssignOperador(_deps(prestadores, asignaciones, opa, opb)).execute(
        AssignOperadorCommand(prestador_id=prestador.id, operador_id=opb, desde=futuro)
    )

    assert dto.operador_id == opa
    assert prestadores.rows[prestador.id].operador_id == opa
    assert _tramos_ordenados(asignaciones) == [
        (opa, date(2025, 1, 1), futuro - timedelta(days=1)),
        (opb, futuro, None),
    ]
    assert await asignaciones.list_vigentes_a(_HOY) == {prestador.id: opa}
    assert await asignaciones.list_vigentes_a(futuro) == {prestador.id: opb}


async def test_reasignar_antes_de_un_tramo_futuro_no_deja_solapes() -> None:
    """Escenario del hallazgo F4: opb programado a futuro y después opc desde
    una fecha anterior — el tramo de opb se borra y el de opa se recorta."""
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()
    opa, opb, opc = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    prestador = _prestador(opa)
    prestadores.rows[prestador.id] = prestador
    _tramo_abierto(asignaciones, prestador, opa, date(2025, 1, 1))
    use_case = AssignOperador(_deps(prestadores, asignaciones, opa, opb, opc))
    lejos = _HOY + timedelta(days=30)
    cerca = _HOY + timedelta(days=1)

    await use_case.execute(
        AssignOperadorCommand(prestador_id=prestador.id, operador_id=opb, desde=lejos)
    )
    await use_case.execute(
        AssignOperadorCommand(prestador_id=prestador.id, operador_id=opc, desde=cerca)
    )

    assert _tramos_ordenados(asignaciones) == [
        (opa, date(2025, 1, 1), _HOY),
        (opc, cerca, None),
    ]
    assert prestadores.rows[prestador.id].operador_id == opa


async def test_rechaza_operador_inexistente_sin_tocar_nada() -> None:
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()
    opa = uuid.uuid4()
    prestador = _prestador(opa)
    prestadores.rows[prestador.id] = prestador

    with pytest.raises(OperadorNoEncontradoError):
        await AssignOperador(_deps(prestadores, asignaciones, opa)).execute(
            AssignOperadorCommand(prestador_id=prestador.id, operador_id=uuid.uuid4(), desde=_HOY)
        )

    assert prestadores.rows[prestador.id].operador_id == opa
    assert asignaciones.rows == {}
