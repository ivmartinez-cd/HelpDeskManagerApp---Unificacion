"""Round-trip del repo de coberturas temporales de turnos (ADR-013)."""

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.turnos.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_casilla_repository import (
    SqlAlchemyCasillaRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_slot_repository import (
    SqlAlchemySlotRepository,
)
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride

from .test_sqlalchemy_turnos_repositories import _app_user, _casilla, _slot


async def test_cobertura_alcance_total_round_trip(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAsignacionOverrideRepository(db_session)
    ausente = await _app_user(db_session, full_name="Ausente")
    reemplazante = await _app_user(db_session, full_name="Reemplazante")
    creador = await _app_user(db_session, full_name="Creador")

    override: AsignacionOverride[uuid.UUID, uuid.UUID] = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=ausente,
        operador_reemplazante_id=reemplazante,
        desde=date(2026, 8, 24),
        hasta=date(2026, 8, 28),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo="vacaciones",
        created_by_user_id=creador,
    )
    await repo.create(override)

    encontrada = await repo.get_by_id(override.id)
    assert encontrada is not None
    assert encontrada.alcance == "TOTAL"
    assert encontrada.operador_reemplazante_id == reemplazante

    activas = await repo.list_activos_por_ausente(ausente)
    assert [o.id for o in activas] == [override.id]


async def test_cobertura_alcance_parcial_por_slots(db_session: AsyncSession) -> None:
    casillas = SqlAlchemyCasillaRepository(db_session)
    slots = SqlAlchemySlotRepository(db_session)
    casilla = _casilla("INSUMOS")
    await casillas.add(casilla)
    slot_a = _slot(casilla.id, dia_semana=0, hora=8)
    slot_b = _slot(casilla.id, dia_semana=1, hora=8)
    await slots.add(slot_a)
    await slots.add(slot_b)

    repo = SqlAlchemyAsignacionOverrideRepository(db_session)
    ausente = await _app_user(db_session)
    reemplazante = await _app_user(db_session)
    creador = await _app_user(db_session)

    override: AsignacionOverride[uuid.UUID, uuid.UUID] = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=ausente,
        operador_reemplazante_id=reemplazante,
        desde=date(2026, 8, 24),
        hasta=date(2026, 8, 28),
        alcance=frozenset({slot_a.id, slot_b.id}),
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=creador,
    )
    await repo.create(override)

    encontrada = await repo.get_by_id(override.id)
    assert encontrada is not None
    assert encontrada.alcance == frozenset({slot_a.id, slot_b.id})


async def test_list_activos_por_ausentes_batch(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAsignacionOverrideRepository(db_session)
    ausente1 = await _app_user(db_session, full_name="Ausente Uno")
    ausente2 = await _app_user(db_session, full_name="Ausente Dos")
    reemplazante = await _app_user(db_session, full_name="Reemplazante")
    creador = await _app_user(db_session, full_name="Creador")

    for ausente in (ausente1, ausente2):
        await repo.create(
            AsignacionOverride(
                id=uuid.uuid4(),
                operador_ausente_id=ausente,
                operador_reemplazante_id=reemplazante,
                desde=date(2026, 8, 24),
                hasta=date(2026, 8, 28),
                alcance="TOTAL",
                estado="ACTIVA",
                motivo=None,
                created_by_user_id=creador,
            )
        )
    cancelada = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=ausente1,
        operador_reemplazante_id=reemplazante,
        desde=date(2026, 9, 1),
        hasta=date(2026, 9, 5),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=creador,
    )
    await repo.create(cancelada)
    await repo.cancelar(cancelada.id)

    resultado = await repo.list_activos_por_ausentes([ausente1, ausente2, uuid.uuid4()])

    assert set(resultado) == {ausente1, ausente2}
    assert len(resultado[ausente1]) == 1  # la cancelada no cuenta
    assert len(resultado[ausente2]) == 1


async def test_update_reemplaza_alcance_de_total_a_parcial(db_session: AsyncSession) -> None:
    casillas = SqlAlchemyCasillaRepository(db_session)
    slots = SqlAlchemySlotRepository(db_session)
    casilla = _casilla("ST")
    await casillas.add(casilla)
    slot = _slot(casilla.id, dia_semana=0, hora=9)
    await slots.add(slot)

    repo = SqlAlchemyAsignacionOverrideRepository(db_session)
    ausente = await _app_user(db_session)
    reemplazante = await _app_user(db_session)
    creador = await _app_user(db_session)
    override: AsignacionOverride[uuid.UUID, uuid.UUID] = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=ausente,
        operador_reemplazante_id=reemplazante,
        desde=date(2026, 8, 24),
        hasta=date(2026, 8, 28),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=creador,
    )
    await repo.create(override)

    override.alcance = frozenset({slot.id})
    override.hasta = date(2026, 8, 30)
    await repo.update(override)

    actualizada = await repo.get_by_id(override.id)
    assert actualizada is not None
    assert actualizada.alcance == frozenset({slot.id})
    assert actualizada.hasta == date(2026, 8, 30)


async def test_cancelar_no_borra_el_registro(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAsignacionOverrideRepository(db_session)
    ausente = await _app_user(db_session)
    reemplazante = await _app_user(db_session)
    creador = await _app_user(db_session)
    override: AsignacionOverride[uuid.UUID, uuid.UUID] = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=ausente,
        operador_reemplazante_id=reemplazante,
        desde=date(2026, 8, 24),
        hasta=date(2026, 8, 28),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=creador,
    )
    await repo.create(override)

    await repo.cancelar(override.id)

    cancelada = await repo.get_by_id(override.id)
    assert cancelada is not None
    assert cancelada.estado == "CANCELADA"
    assert await repo.list_activos_por_ausente(ausente) == []


async def test_intercambio_id_round_trip_y_list_by_intercambio(db_session: AsyncSession) -> None:
    """ADR-026: las dos mitades comparten `intercambio_id`; una cobertura común lo deja en None."""
    repo = SqlAlchemyAsignacionOverrideRepository(db_session)
    majo = await _app_user(db_session, full_name="Majo")
    luna = await _app_user(db_session, full_name="Luna")
    creador = await _app_user(db_session, full_name="Creador")
    intercambio_id = uuid.uuid4()

    for ausente, cubre in ((majo, luna), (luna, majo)):
        await repo.create(
            AsignacionOverride(
                id=uuid.uuid4(),
                operador_ausente_id=ausente,
                operador_reemplazante_id=cubre,
                desde=date(2026, 8, 20),
                hasta=date(2026, 8, 20),
                alcance="TOTAL",
                estado="ACTIVA",
                motivo="Intercambio",
                created_by_user_id=creador,
                intercambio_id=intercambio_id,
            )
        )
    comun = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=majo,
        operador_reemplazante_id=creador,
        desde=date(2026, 9, 1),
        hasta=date(2026, 9, 1),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=creador,
    )
    await repo.create(comun)

    par = await repo.list_by_intercambio(intercambio_id)
    assert {(o.operador_ausente_id, o.operador_reemplazante_id) for o in par} == {
        (majo, luna),
        (luna, majo),
    }
    assert all(o.intercambio_id == intercambio_id for o in par)
    leida = await repo.get_by_id(comun.id)
    assert leida is not None and leida.intercambio_id is None
    assert await repo.list_by_intercambio(uuid.uuid4()) == []
