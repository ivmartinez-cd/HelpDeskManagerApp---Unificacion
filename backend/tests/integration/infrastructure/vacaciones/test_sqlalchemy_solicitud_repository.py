import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.empleado import Empleado, EstadoEmpleado
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    FiltrosSolicitudes,
    RangoSolapado,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_solicitud_repository import (
    SqlAlchemySolicitudRepository,
)
from tests.integration.infrastructure.vacaciones.conftest import make_empleado_entity


def _solicitud(
    empleado_id: uuid.UUID, start: date, end: date, status: EstadoSolicitud
) -> Solicitud:
    return Solicitud(
        id=uuid.uuid4(),
        empleado_id=empleado_id,
        start_date=start,
        end_date=end,
        days_requested=(end - start).days + 1,
        charged_to_year=start.year,
        reason=None,
        status=status,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_solape_incluye_bordes_y_excluye_adyacentes(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemySolicitudRepository(db_session)
    await repo.add(
        _solicitud(empleado.id, date(2026, 9, 7), date(2026, 9, 11), EstadoSolicitud.APPROVED)
    )

    borde = await repo.list_activas_solapadas_de_empleados(
        [empleado.id], RangoSolapado(start=date(2026, 9, 11), end=date(2026, 9, 15))
    )
    assert len(borde) == 1

    adyacente = await repo.list_activas_solapadas_de_empleados(
        [empleado.id], RangoSolapado(start=date(2026, 9, 12), end=date(2026, 9, 15))
    )
    assert adyacente == []


@pytest.mark.asyncio
async def test_rechazadas_no_cuentan_como_activas(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemySolicitudRepository(db_session)
    await repo.add(
        _solicitud(empleado.id, date(2026, 9, 7), date(2026, 9, 11), EstadoSolicitud.REJECTED)
    )
    activas = await repo.list_activas_de_empleado(empleado.id)
    assert activas == []


@pytest.mark.asyncio
async def test_rangos_por_cargo_excluye_al_solicitante_y_a_inactivos(
    db_session: AsyncSession, empleado: Empleado, sector_id: uuid.UUID
) -> None:
    empleados = SqlAlchemyEmpleadoRepository(db_session)
    solicitudes = SqlAlchemySolicitudRepository(db_session)

    colega = make_empleado_entity(sector_id, empleado.cargo_id)
    inactivo = make_empleado_entity(
        sector_id, empleado.cargo_id, status=EstadoEmpleado.INACTIVE
    )
    await empleados.add(colega)
    await empleados.add(inactivo)

    rango = (date(2026, 9, 7), date(2026, 9, 11))
    for e in (empleado, colega, inactivo):
        await solicitudes.add(_solicitud(e.id, rango[0], rango[1], EstadoSolicitud.APPROVED))

    rangos = await solicitudes.list_rangos_activos_por_cargo(
        empleado.cargo_id, empleado.id, RangoSolapado(start=rango[0], end=rango[1])
    )
    # Solo el colega activo: ni el propio solicitante ni el inactivo.
    assert rangos == [rango]


@pytest.mark.asyncio
async def test_calendario_filtra_por_departamento(
    db_session: AsyncSession, empleado: Empleado, cargo_id: uuid.UUID
) -> None:
    import uuid as _uuid

    from src.modules.auth.infrastructure.models.user_model import Department

    otro_sector = Department(
        id=_uuid.uuid4(), name=f"Otro {_uuid.uuid4().hex[:8]}", is_active=True, color="#000000"
    )
    db_session.add(otro_sector)
    await db_session.flush()

    empleados = SqlAlchemyEmpleadoRepository(db_session)
    ajeno = make_empleado_entity(otro_sector.id, cargo_id)
    await empleados.add(ajeno)

    solicitudes = SqlAlchemySolicitudRepository(db_session)
    await solicitudes.add(
        _solicitud(empleado.id, date(2026, 9, 7), date(2026, 9, 11), EstadoSolicitud.APPROVED)
    )
    await solicitudes.add(
        _solicitud(ajeno.id, date(2026, 9, 7), date(2026, 9, 11), EstadoSolicitud.PENDING)
    )

    del_sector = await solicitudes.list_activas_en_rango(
        date(2026, 9, 1), date(2026, 9, 30), empleado.department_id
    )
    assert {s.empleado_id for s in del_sector} == {empleado.id}

    globales = await solicitudes.list_activas_en_rango(date(2026, 9, 1), date(2026, 9, 30), None)
    assert {s.empleado_id for s in globales} == {empleado.id, ajeno.id}


@pytest.mark.asyncio
async def test_list_activas_en_rango_incluye_las_que_ya_empezaron(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemySolicitudRepository(db_session)
    await repo.add(
        _solicitud(empleado.id, date(2026, 8, 24), date(2026, 8, 28), EstadoSolicitud.APPROVED)
    )

    vigente_hoy = await repo.list_activas_en_rango(date(2026, 8, 25), date(2026, 9, 15), None)
    assert len(vigente_hoy) == 1

    ya_terminada = await repo.list_activas_en_rango(date(2026, 8, 29), date(2026, 9, 15), None)
    assert ya_terminada == []


@pytest.mark.asyncio
async def test_list_filtradas_por_fecha_incluye_las_que_ya_empezaron(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemySolicitudRepository(db_session)
    await repo.add(
        _solicitud(empleado.id, date(2026, 8, 24), date(2026, 8, 28), EstadoSolicitud.APPROVED)
    )

    vigente_hoy = await repo.list_filtradas(
        FiltrosSolicitudes(desde=date(2026, 8, 25), hasta=date(2026, 9, 15))
    )
    assert len(vigente_hoy) == 1

    ya_terminada = await repo.list_filtradas(
        FiltrosSolicitudes(desde=date(2026, 8, 29), hasta=date(2026, 9, 15))
    )
    assert ya_terminada == []
