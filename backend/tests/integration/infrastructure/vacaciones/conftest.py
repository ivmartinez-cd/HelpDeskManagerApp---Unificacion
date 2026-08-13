import uuid
from datetime import date

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import Department
from src.modules.vacaciones.domain.entities.empleado import Empleado, EstadoEmpleado
from src.modules.vacaciones.infrastructure.models.cargo_model import VacacionesCargoModel
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)


@pytest_asyncio.fixture
async def sector_id(db_session: AsyncSession) -> uuid.UUID:
    department = Department(
        id=uuid.uuid4(), name=f"Sector {uuid.uuid4().hex[:8]}", is_active=True, color="#2563eb"
    )
    db_session.add(department)
    await db_session.flush()
    return department.id


@pytest_asyncio.fixture
async def cargo_id(db_session: AsyncSession) -> uuid.UUID:
    cargo = VacacionesCargoModel(
        id=uuid.uuid4(), name=f"Cargo {uuid.uuid4().hex[:8]}", max_simultaneos=None
    )
    db_session.add(cargo)
    await db_session.flush()
    return cargo.id


def make_empleado_entity(
    sector_id: uuid.UUID, cargo_id: uuid.UUID, **overrides: object
) -> Empleado:
    sufijo = uuid.uuid4().hex[:8]
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "first_name": "Laura",
        "last_name": "Pérez",
        "email": f"lperez-{sufijo}@canal.com",
        "hire_date": date(2019, 3, 15),
        "annual_vacation_days": 22,
        "status": EstadoEmpleado.ACTIVE,
        "color": "#2563eb",
        "department_id": sector_id,
        "cargo_id": cargo_id,
        "user_id": None,
    }
    defaults.update(overrides)
    return Empleado(**defaults)  # type: ignore[arg-type]


@pytest_asyncio.fixture
async def empleado(
    db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> Empleado:
    entity = make_empleado_entity(sector_id, cargo_id)
    await SqlAlchemyEmpleadoRepository(db_session).add(entity)
    return entity
