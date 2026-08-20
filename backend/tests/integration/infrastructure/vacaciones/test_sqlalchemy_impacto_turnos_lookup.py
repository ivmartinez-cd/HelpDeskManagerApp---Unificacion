"""Puerto vacaciones → turnos (ADR-025) contra Postgres de test."""

import uuid
from datetime import date, time

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.turnos.infrastructure.models.turno_models import (
    TurnoAsignacionModel,
    TurnoCasillaModel,
    TurnoSlotModel,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_impacto_turnos_lookup import (  # noqa: E501
    SqlAlchemyImpactoTurnosLookup,
)


async def _user(session: AsyncSession) -> uuid.UUID:
    user = AppUser(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@test.local",
        password_hash="x",
        full_name="Majo",
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user.id


async def _slot_con_asignacion(
    session: AsyncSession, user_id: uuid.UUID, *, dia_semana: int, vigente_hasta: date | None
) -> None:
    casilla = TurnoCasillaModel(id=uuid.uuid4(), nombre=f"C-{uuid.uuid4()}")
    slot = TurnoSlotModel(
        id=uuid.uuid4(),
        casilla=casilla,
        hora_inicio=time(8),
        hora_fin=time(11),
        dia_semana=dia_semana,
    )
    session.add_all([casilla, slot])
    await session.flush()
    session.add(
        TurnoAsignacionModel(
            slot_id=slot.id,
            user_id=user_id,
            vigente_desde=date(2026, 1, 1),
            vigente_hasta=vigente_hasta,
        )
    )
    await session.flush()


async def test_detecta_franjas_vigentes_cuyo_dia_cae_en_el_rango(db_session: AsyncSession) -> None:
    lookup = SqlAlchemyImpactoTurnosLookup(db_session)
    majo = await _user(db_session)
    await _slot_con_asignacion(db_session, majo, dia_semana=2, vigente_hasta=None)  # miércoles

    # 24-28/08/2026 es lunes a viernes: incluye el miércoles
    assert await lookup.tiene_turnos_en(majo, date(2026, 8, 24), date(2026, 8, 28)) is True
    # 29-30/08/2026 es sábado y domingo: no hay miércoles en el rango
    assert await lookup.tiene_turnos_en(majo, date(2026, 8, 29), date(2026, 8, 30)) is False
    # Otro usuario sin franjas
    assert await lookup.tiene_turnos_en(uuid.uuid4(), date(2026, 8, 24), date(2026, 8, 28)) is False


async def test_ignora_asignaciones_ya_cerradas_antes_del_rango(db_session: AsyncSession) -> None:
    lookup = SqlAlchemyImpactoTurnosLookup(db_session)
    majo = await _user(db_session)
    await _slot_con_asignacion(db_session, majo, dia_semana=0, vigente_hasta=date(2026, 6, 30))

    assert await lookup.tiene_turnos_en(majo, date(2026, 8, 24), date(2026, 8, 28)) is False
    assert await lookup.tiene_turnos_en(majo, date(2026, 6, 29), date(2026, 7, 3)) is True
