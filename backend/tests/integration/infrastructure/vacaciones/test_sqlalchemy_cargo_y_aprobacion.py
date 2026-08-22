"""SqlAlchemyCargoRepository y SqlAlchemyAprobacionRepository contra Postgres real."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.vacaciones.domain.entities.aprobacion import Aprobacion, Decision
from src.modules.vacaciones.domain.entities.cargo import Cargo
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_aprobacion_repository import (
    SqlAlchemyAprobacionRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_cargo_repository import (
    SqlAlchemyCargoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_solicitud_repository import (
    SqlAlchemySolicitudRepository,
)
from tests.integration.infrastructure.vacaciones.conftest import make_empleado_entity


def _cargo(name: str, max_simultaneos: int | None = None) -> Cargo:
    return Cargo(id=uuid.uuid4(), name=name, max_simultaneos=max_simultaneos)


async def test_cargo_add_get_by_id_y_get_by_name(db_session: AsyncSession) -> None:
    repo = SqlAlchemyCargoRepository(db_session)
    nombre = f"Operador {uuid.uuid4().hex[:8]}"
    cargo = _cargo(nombre, max_simultaneos=2)
    await repo.add(cargo)

    por_id = await repo.get_by_id(cargo.id)
    assert por_id is not None
    assert por_id.max_simultaneos == 2
    por_nombre = await repo.get_by_name(nombre)
    assert por_nombre is not None
    assert por_nombre.id == cargo.id
    assert await repo.get_by_id(uuid.uuid4()) is None
    assert await repo.get_by_name(f"inexistente-{uuid.uuid4().hex}") is None


async def test_cargo_list_all_ordena_por_nombre(db_session: AsyncSession) -> None:
    repo = SqlAlchemyCargoRepository(db_session)
    prefijo = uuid.uuid4().hex[:8]
    zeta = _cargo(f"{prefijo} Zeta")
    alfa = _cargo(f"{prefijo} Alfa")
    await repo.add(zeta)
    await repo.add(alfa)

    nombres = [c.name for c in await repo.list_all() if c.name.startswith(prefijo)]
    assert nombres == [alfa.name, zeta.name]


async def test_cargo_count_empleados_cuenta_solo_los_del_cargo(
    db_session: AsyncSession, empleado: Empleado, sector_id: uuid.UUID
) -> None:
    repo = SqlAlchemyCargoRepository(db_session)
    otro = _cargo(f"Otro {uuid.uuid4().hex[:8]}")
    await repo.add(otro)
    await SqlAlchemyEmpleadoRepository(db_session).add(make_empleado_entity(sector_id, otro.id))

    assert await repo.count_empleados(empleado.cargo_id) == 1
    assert await repo.count_empleados(otro.id) == 1
    assert await repo.count_empleados(uuid.uuid4()) == 0


async def test_cargo_save_y_delete_idempotentes(db_session: AsyncSession) -> None:
    repo = SqlAlchemyCargoRepository(db_session)
    cargo = _cargo(f"Soporte {uuid.uuid4().hex[:8]}")
    await repo.add(cargo)

    cargo.name = f"Soporte N2 {uuid.uuid4().hex[:8]}"
    cargo.max_simultaneos = 3
    await repo.save(cargo)
    leido = await repo.get_by_id(cargo.id)
    assert leido is not None
    assert (leido.name, leido.max_simultaneos) == (cargo.name, 3)

    fantasma = _cargo("fantasma")
    await repo.save(fantasma)
    assert await repo.get_by_id(fantasma.id) is None
    await repo.delete(fantasma.id)

    await repo.delete(cargo.id)
    assert await repo.get_by_id(cargo.id) is None


async def _solicitud(db_session: AsyncSession, empleado_id: uuid.UUID, start: date) -> Solicitud:
    solicitud = Solicitud(
        id=uuid.uuid4(),
        empleado_id=empleado_id,
        start_date=start,
        end_date=start,
        days_requested=1,
        charged_to_year=start.year,
        reason=None,
        status=EstadoSolicitud.PENDING,
        created_at=datetime.now(UTC),
    )
    await SqlAlchemySolicitudRepository(db_session).add(solicitud)
    return solicitud


def _aprobacion(
    solicitud_id: uuid.UUID, decision: Decision, approver: uuid.UUID | None
) -> Aprobacion:
    return Aprobacion(
        id=uuid.uuid4(),
        solicitud_id=solicitud_id,
        approver_user_id=approver,
        decision=decision,
        comment="ok" if decision is Decision.APPROVED else None,
        created_at=datetime.now(UTC),
    )


async def test_aprobacion_add_y_list_por_solicitud(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    user = AppUser(
        id=uuid.uuid4(),
        email=f"aprobador-{uuid.uuid4().hex[:8]}@canal.com",
        password_hash="x",
        full_name="Aprobador Test",
    )
    db_session.add(user)
    await db_session.flush()
    solicitud = await _solicitud(db_session, empleado.id, date(2026, 9, 7))
    repo = SqlAlchemyAprobacionRepository(db_session)
    await repo.add(_aprobacion(solicitud.id, Decision.REJECTED, None))
    await repo.add(_aprobacion(solicitud.id, Decision.APPROVED, user.id))

    historial = await repo.list_por_solicitud(solicitud.id)
    assert {a.decision for a in historial} == {Decision.APPROVED, Decision.REJECTED}
    aprobada = next(a for a in historial if a.decision is Decision.APPROVED)
    assert aprobada.approver_user_id == user.id
    assert aprobada.comment == "ok"
    assert await repo.list_por_solicitud(uuid.uuid4()) == []


async def test_aprobacion_list_por_solicitudes_agrupa_y_lista_vacia(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemyAprobacionRepository(db_session)
    s1 = await _solicitud(db_session, empleado.id, date(2026, 9, 7))
    s2 = await _solicitud(db_session, empleado.id, date(2026, 10, 7))
    sin_historial = await _solicitud(db_session, empleado.id, date(2026, 11, 7))
    await repo.add(_aprobacion(s1.id, Decision.APPROVED, None))
    await repo.add(_aprobacion(s1.id, Decision.REJECTED, None))
    await repo.add(_aprobacion(s2.id, Decision.APPROVED, None))

    assert await repo.list_por_solicitudes([]) == {}
    agrupado = await repo.list_por_solicitudes([s1.id, s2.id, sin_historial.id])
    assert set(agrupado) == {s1.id, s2.id}
    assert len(agrupado[s1.id]) == 2
    assert len(agrupado[s2.id]) == 1
