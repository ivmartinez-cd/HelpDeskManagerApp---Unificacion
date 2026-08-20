"""Round-trip de grillas variantes y del lookup de ausencias contra Postgres de test."""

import uuid
from datetime import date, time

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser, Department
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante, VarianteSlot
from src.modules.turnos.infrastructure.repositories.sqlalchemy_ausencias_lookup import (
    SqlAlchemyAusenciasLookup,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_casilla_repository import (
    SqlAlchemyCasillaRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_grilla_variante_repository import (  # noqa: E501
    SqlAlchemyGrillaVarianteRepository,
)
from src.modules.vacaciones.infrastructure.models.cargo_model import VacacionesCargoModel
from src.modules.vacaciones.infrastructure.models.empleado_model import VacacionesEmpleadoModel
from src.modules.vacaciones.infrastructure.models.solicitud_model import (
    VacacionesSolicitudModel,
)


async def _app_user(session: AsyncSession, full_name: str = "Ana Prueba") -> uuid.UUID:
    user = AppUser(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@test.local",
        password_hash="x",
        full_name=full_name,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user.id


async def _casilla(session: AsyncSession, nombre: str) -> Casilla:
    casilla = Casilla(id=uuid.uuid4(), nombre=nombre, color=None, sort_order=0, is_active=True)
    await SqlAlchemyCasillaRepository(session).add(casilla)
    return casilla


def _franja(casilla_id: uuid.UUID, inicio: int, fin: int, *users: uuid.UUID) -> VarianteSlot:
    return VarianteSlot(
        id=uuid.uuid4(),
        casilla_id=casilla_id,
        dia_semana=0,
        hora_inicio=time(inicio),
        hora_fin=time(fin),
        sort_order=0,
        user_ids=list(users),
    )


def _variante(
    creador: uuid.UUID, slots: list[VarianteSlot], *, desde: date, hasta: date
) -> GrillaVariante:
    return GrillaVariante(
        id=uuid.uuid4(),
        motivo="Vacaciones",
        origen_texto="test",
        desde=desde,
        hasta=hasta,
        estado="ACTIVA",
        created_by_user_id=creador,
        slots=slots,
    )


async def test_variante_round_trip_con_franjas_y_asignaciones(db_session: AsyncSession) -> None:
    repo = SqlAlchemyGrillaVarianteRepository(db_session)
    creador = await _app_user(db_session)
    mariano = await _app_user(db_session, "Mariano")
    insumos = await _casilla(db_session, f"INSUMOS-{uuid.uuid4()}")
    variante = _variante(
        creador,
        [_franja(insumos.id, 8, 11, mariano), _franja(insumos.id, 11, 13)],
        desde=date(2026, 8, 24),
        hasta=date(2026, 8, 28),
    )

    await repo.create(variante)
    leida = await repo.get_by_id(variante.id)

    assert leida is not None
    assert (leida.motivo, leida.origen_texto, leida.estado) == ("Vacaciones", "test", "ACTIVA")
    assert [(s.hora_inicio, s.user_ids) for s in leida.slots] == [
        (time(8), [mariano]),
        (time(11), []),
    ]


async def test_find_vigente_ignora_canceladas_y_fuera_de_rango(db_session: AsyncSession) -> None:
    repo = SqlAlchemyGrillaVarianteRepository(db_session)
    creador = await _app_user(db_session)
    insumos = await _casilla(db_session, f"INSUMOS-{uuid.uuid4()}")
    # Rangos fuera de cualquier dato ya existente en la DB de test
    activa = _variante(
        creador, [_franja(insumos.id, 8, 9)], desde=date(2031, 3, 2), hasta=date(2031, 3, 6)
    )
    cancelada = _variante(
        creador, [_franja(insumos.id, 8, 9)], desde=date(2031, 3, 9), hasta=date(2031, 3, 13)
    )
    await repo.create(activa)
    await repo.create(cancelada)
    await repo.cancelar(cancelada.id)

    assert (await repo.find_vigente(date(2031, 3, 4))) == activa
    assert (await repo.find_vigente(date(2031, 3, 10))) is None
    assert (await repo.find_vigente(date(2031, 3, 7))) is None
    assert [v.id for v in await repo.list_activas() if v.id in (activa.id, cancelada.id)] == [
        activa.id
    ]


async def test_update_reemplaza_franjas_in_place(db_session: AsyncSession) -> None:
    repo = SqlAlchemyGrillaVarianteRepository(db_session)
    creador = await _app_user(db_session)
    luna = await _app_user(db_session, "Luna")
    insumos = await _casilla(db_session, f"INSUMOS-{uuid.uuid4()}")
    variante = _variante(
        creador, [_franja(insumos.id, 8, 11)], desde=date(2031, 4, 7), hasta=date(2031, 4, 11)
    )
    await repo.create(variante)

    variante.hasta = date(2031, 4, 12)
    variante.slots = [_franja(insumos.id, 9, 12, luna)]
    await repo.update(variante)
    leida = await repo.get_by_id(variante.id)

    assert leida is not None
    assert leida.hasta == date(2031, 4, 12)
    assert [(s.hora_inicio, s.user_ids) for s in leida.slots] == [(time(9), [luna])]


async def test_ausencias_lookup_devuelve_solo_aprobadas_de_usuarios_vinculados(
    db_session: AsyncSession,
) -> None:
    luna = await _app_user(db_session, "Luna")
    otro = await _app_user(db_session, "Otro")
    sector = Department(id=uuid.uuid4(), name=f"Sector-{uuid.uuid4()}", color="#2563eb")
    cargo = VacacionesCargoModel(id=uuid.uuid4(), name=f"Cargo-{uuid.uuid4()}")
    db_session.add_all([sector, cargo])
    await db_session.flush()
    empleado = VacacionesEmpleadoModel(
        id=uuid.uuid4(),
        first_name="Luna",
        last_name="Torres",
        email=f"{uuid.uuid4()}@test.local",
        hire_date=date(2020, 1, 1),
        annual_vacation_days=14,
        department_id=sector.id,
        cargo_id=cargo.id,
        user_id=luna,
    )
    db_session.add(empleado)
    await db_session.flush()
    db_session.add_all(
        [
            VacacionesSolicitudModel(
                empleado_id=empleado.id,
                start_date=date(2031, 5, 5),
                end_date=date(2031, 5, 9),
                days_requested=5,
                status="APPROVED",
            ),
            VacacionesSolicitudModel(
                empleado_id=empleado.id,
                start_date=date(2031, 5, 12),
                end_date=date(2031, 5, 16),
                days_requested=5,
                status="PENDING",
            ),
        ]
    )
    await db_session.flush()

    lookup = SqlAlchemyAusenciasLookup(db_session)
    ausencias = await lookup.ausencias_aprobadas_en(
        [luna, otro], date(2031, 5, 1), date(2031, 5, 31)
    )

    assert [(a.user_id, a.desde, a.hasta) for a in ausencias] == [
        (luna, date(2031, 5, 5), date(2031, 5, 9))
    ]
    assert await lookup.ausencias_aprobadas_en([], date(2031, 5, 1), date(2031, 5, 31)) == []
