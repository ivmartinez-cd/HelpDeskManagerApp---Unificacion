import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.domain.entities.empleado import Empleado, EstadoEmpleado
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud
from src.modules.vacaciones.domain.repositories.empleado_repository import FiltrosEmpleados
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_ciclo_repository import (
    SqlAlchemyCicloRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_solicitud_repository import (
    SqlAlchemySolicitudRepository,
)
from tests.integration.infrastructure.vacaciones.conftest import make_empleado_entity


@pytest.mark.asyncio
async def test_add_y_get_roundtrip(db_session: AsyncSession, empleado: Empleado) -> None:
    repo = SqlAlchemyEmpleadoRepository(db_session)
    leido = await repo.get_by_id(empleado.id)
    assert leido is not None
    assert leido.email == empleado.email
    assert leido.hire_date == date(2019, 3, 15)
    assert leido.status is EstadoEmpleado.ACTIVE


@pytest.mark.asyncio
async def test_busqueda_por_nombre_y_por_cargo(
    db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    repo = SqlAlchemyEmpleadoRepository(db_session)
    await repo.add(
        make_empleado_entity(sector_id, cargo_id, first_name="Zulema", last_name="Zas")
    )
    por_nombre = await repo.list_filtrados(FiltrosEmpleados(search="zulema"))
    assert any(e.first_name == "Zulema" for e in por_nombre)

    filtro_sector = await repo.list_filtrados(FiltrosEmpleados(department_id=sector_id))
    assert all(e.department_id == sector_id for e in filtro_sector)
    assert len(filtro_sector) == 1


@pytest.mark.asyncio
async def test_delete_cascadea_ciclos_y_solicitudes(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    ciclos = SqlAlchemyCicloRepository(db_session)
    solicitudes = SqlAlchemySolicitudRepository(db_session)
    await ciclos.add(
        Ciclo(
            id=uuid.uuid4(),
            empleado_id=empleado.id,
            year=2026,
            annual_days=14,
            carry_over=0,
            is_open=True,
            opened_at=None,
        )
    )
    solicitud_id = uuid.uuid4()
    await solicitudes.add(
        Solicitud(
            id=solicitud_id,
            empleado_id=empleado.id,
            start_date=date(2026, 9, 7),
            end_date=date(2026, 9, 11),
            days_requested=7,
            charged_to_year=2026,
            reason=None,
            status=EstadoSolicitud.PENDING,
            created_at=datetime.now(UTC),
        )
    )

    await SqlAlchemyEmpleadoRepository(db_session).delete(empleado.id)

    assert await ciclos.get(empleado.id, 2026) is None
    assert await solicitudes.get_by_id(solicitud_id) is None
