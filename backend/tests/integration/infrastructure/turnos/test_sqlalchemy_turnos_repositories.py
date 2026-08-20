"""Round-trips de los cuatro repos de turnos contra Postgres de test."""

import uuid
from datetime import date, time

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.infrastructure.models.turno_models import TurnoAsignacionModel
from src.modules.turnos.infrastructure.repositories.sqlalchemy_asignacion_repository import (
    SqlAlchemyAsignacionRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_casilla_repository import (
    SqlAlchemyCasillaRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_slot_repository import (
    SqlAlchemySlotRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_user_provider import (
    SqlAlchemyUserProvider,
)


def _casilla(nombre: str, *, sort_order: int = 0, is_active: bool = True) -> Casilla:
    return Casilla(
        id=uuid.uuid4(), nombre=nombre, color="#123456", sort_order=sort_order, is_active=is_active
    )


def _slot(casilla_id: uuid.UUID, *, dia_semana: int = 0, hora: int = 9) -> Slot:
    return Slot(
        id=uuid.uuid4(),
        casilla_id=casilla_id,
        hora_inicio=time(hora, 0),
        hora_fin=time(hora + 1, 0),
        dia_semana=dia_semana,
        sort_order=0,
    )


async def _app_user(
    session: AsyncSession, *, full_name: str = "Ana Prueba", is_active: bool = True
) -> uuid.UUID:
    user = AppUser(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@test.local",
        password_hash="x",
        full_name=full_name,
        is_active=is_active,
    )
    session.add(user)
    await session.flush()
    return user.id


async def test_casilla_round_trip_y_filtro_de_inactivas(db_session: AsyncSession) -> None:
    repo = SqlAlchemyCasillaRepository(db_session)
    activa = _casilla("Mesa", sort_order=2)
    inactiva = _casilla("Vieja", sort_order=1, is_active=False)
    await repo.add(activa)
    await repo.add(inactiva)

    encontrada = await repo.get_by_id(activa.id)
    assert encontrada is not None and encontrada.nombre == "Mesa"

    assert [c.nombre for c in await repo.list_all()] == ["Mesa"]
    todas = await repo.list_all(include_inactive=True)
    assert [c.nombre for c in todas] == ["Vieja", "Mesa"]  # ordena por sort_order


async def test_casilla_save_delete_y_get_inexistente(db_session: AsyncSession) -> None:
    repo = SqlAlchemyCasillaRepository(db_session)
    casilla = _casilla("Mesa")
    await repo.add(casilla)

    casilla.nombre = "Mesa Norte"
    casilla.is_active = False
    await repo.save(casilla)
    guardada = await repo.get_by_id(casilla.id)
    assert guardada is not None and guardada.nombre == "Mesa Norte" and not guardada.is_active

    await repo.delete(casilla.id)
    assert await repo.get_by_id(casilla.id) is None
    # save de un id inexistente es no-op, no explota
    await repo.save(casilla)


async def test_slot_round_trip_orden_y_delete(db_session: AsyncSession) -> None:
    casillas = SqlAlchemyCasillaRepository(db_session)
    repo = SqlAlchemySlotRepository(db_session)
    casilla = _casilla("Mesa")
    await casillas.add(casilla)
    tarde = _slot(casilla.id, dia_semana=0, hora=14)
    temprano = _slot(casilla.id, dia_semana=0, hora=8)
    await repo.add(tarde)
    await repo.add(temprano)

    assert [s.id for s in await repo.list_by_casilla(casilla.id)] == [temprano.id, tarde.id]
    assert len(await repo.list_all()) == 2

    temprano.hora_fin = time(9, 30)
    await repo.save(temprano)
    guardado = await repo.get_by_id(temprano.id)
    assert guardado is not None and guardado.hora_fin == time(9, 30)

    await repo.delete(tarde.id)
    assert await repo.get_by_id(tarde.id) is None
    await repo.save(tarde)  # no-op sobre id borrado


async def _slot_con_casilla(session: AsyncSession) -> Slot:
    casilla = _casilla(f"Mesa-{uuid.uuid4().hex[:6]}")
    await SqlAlchemyCasillaRepository(session).add(casilla)
    slot = _slot(casilla.id)
    await SqlAlchemySlotRepository(session).add(slot)
    return slot


def _asignacion(
    slot_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    desde: date,
    hasta: date | None = None,
) -> Asignacion:
    return Asignacion(
        id=uuid.uuid4(), slot_id=slot_id, user_id=user_id, vigente_desde=desde, vigente_hasta=hasta
    )


async def test_asignaciones_listados_por_slot_y_por_fecha(db_session: AsyncSession) -> None:
    slot = await _slot_con_casilla(db_session)
    otro_slot = await _slot_con_casilla(db_session)
    repo = SqlAlchemyAsignacionRepository(db_session)
    user_id = await _app_user(db_session)
    vigente = _asignacion(slot.id, user_id, desde=date(2026, 1, 1))
    cerrada = _asignacion(otro_slot.id, user_id, desde=date(2025, 1, 1), hasta=date(2025, 12, 31))
    await repo.replace_for_slot(slot.id, date(2026, 1, 1), [vigente])
    await repo.replace_for_slot(otro_slot.id, date(2025, 1, 1), [cerrada])

    en_2026 = await repo.list_by_slots([slot.id, otro_slot.id], date(2026, 8, 14))
    assert set(en_2026) == {slot.id}
    assert [a.id for a in en_2026[slot.id]] == [vigente.id]

    en_2025 = await repo.list_by_slots([slot.id, otro_slot.id], date(2025, 6, 1))
    assert set(en_2025) == {otro_slot.id}
    assert [a.id for a in en_2025[otro_slot.id]] == [cerrada.id]

    assert await repo.list_by_slots([], date(2026, 8, 14)) == {}

    activas = await repo.list_active_on_date(date(2026, 8, 14))
    assert [a.id for a in activas] == [vigente.id]
    activas_2025 = await repo.list_active_on_date(date(2025, 6, 1))
    assert [a.id for a in activas_2025] == [cerrada.id]


async def test_replace_for_slot_cierra_el_tramo_abierto(db_session: AsyncSession) -> None:
    slot = await _slot_con_casilla(db_session)
    repo = SqlAlchemyAsignacionRepository(db_session)
    user_id = await _app_user(db_session)
    original = _asignacion(slot.id, user_id, desde=date(2026, 1, 1))
    await repo.replace_for_slot(slot.id, date(2026, 1, 1), [original])

    reemplazo = _asignacion(slot.id, user_id, desde=date(2026, 6, 1))
    await repo.replace_for_slot(slot.id, date(2026, 6, 1), [reemplazo])

    antes = await repo.list_by_slots([slot.id], date(2026, 5, 31))
    assert [a.id for a in antes[slot.id]] == [original.id]
    assert antes[slot.id][0].vigente_hasta == date(2026, 5, 31)

    despues = await repo.list_by_slots([slot.id], date(2026, 6, 1))
    assert [a.id for a in despues[slot.id]] == [reemplazo.id]
    assert despues[slot.id][0].vigente_hasta is None


async def test_replace_for_slot_borra_tramos_que_nunca_cubrieron_un_dia(
    db_session: AsyncSession,
) -> None:
    slot = await _slot_con_casilla(db_session)
    repo = SqlAlchemyAsignacionRepository(db_session)
    user_id = await _app_user(db_session)
    # Abierta HOY y reemplazada HOY: cerrarla daría hasta < desde → se borra.
    efimera = _asignacion(slot.id, user_id, desde=date(2026, 8, 14))
    await repo.replace_for_slot(slot.id, date(2026, 8, 14), [efimera])

    reemplazo = _asignacion(slot.id, user_id, desde=date(2026, 8, 14))
    await repo.replace_for_slot(slot.id, date(2026, 8, 14), [reemplazo])

    resultado = await repo.list_by_slots([slot.id], date(2026, 8, 14))
    assert [a.id for a in resultado[slot.id]] == [reemplazo.id]

    await repo.delete_by_slot(slot.id)
    assert await repo.list_by_slots([slot.id], date(2026, 8, 14)) == {}


async def test_no_permite_dos_asignaciones_abiertas_del_mismo_operador_en_el_slot(
    db_session: AsyncSession,
) -> None:
    """Índice único parcial (slot_id, user_id) WHERE vigente_hasta IS NULL -- la
    causa raíz de los operadores duplicados en la tabla de admin ahora es
    imposible a nivel de schema, no solo evitada por el caso de uso."""
    slot = await _slot_con_casilla(db_session)
    user_id = await _app_user(db_session)
    db_session.add(
        TurnoAsignacionModel(
            id=uuid.uuid4(),
            slot_id=slot.id,
            user_id=user_id,
            vigente_desde=date(2026, 8, 14),
            vigente_hasta=None,
        )
    )
    await db_session.flush()

    db_session.add(
        TurnoAsignacionModel(
            id=uuid.uuid4(),
            slot_id=slot.id,
            user_id=user_id,
            vigente_desde=date(2026, 8, 14),
            vigente_hasta=None,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_user_provider_resuelve_ids_y_lista_activos(db_session: AsyncSession) -> None:
    provider = SqlAlchemyUserProvider(db_session)
    ana = await _app_user(db_session, full_name="Ana")
    zoe = await _app_user(db_session, full_name="Zoe")
    await _app_user(db_session, full_name="Baja", is_active=False)

    assert await provider.get_users_by_ids([]) == {}
    por_id = await provider.get_users_by_ids([ana, zoe])
    assert por_id[ana].full_name == "Ana" and por_id[zoe].full_name == "Zoe"

    activos = [u.full_name for u in await provider.list_all_active_users()]
    assert "Baja" not in activos
    assert activos.index("Ana") < activos.index("Zoe")  # ordena por nombre
