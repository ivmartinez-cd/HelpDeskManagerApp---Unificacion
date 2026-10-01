import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from tests.integration.infrastructure.vacaciones.conftest import (  # noqa: F401
    cargo_id,
    make_empleado_entity,
    sector_id,
)


async def crear_usuario(
    db: AsyncSession, *, superadmin: bool = False, activo: bool = True, placeholder: bool = False
) -> uuid.UUID:
    user = AppUser(
        email=f"{uuid.uuid4().hex[:10]}@test.local",
        full_name="Persona Test",
        password_hash="x",
        is_superadmin=superadmin,
        is_active=activo,
        is_placeholder=placeholder,
    )
    db.add(user)
    await db.flush()
    return user.id


async def alta_empleado(
    db: AsyncSession, sector: uuid.UUID, cargo: uuid.UUID, **overrides: object
) -> Empleado:
    empleado = make_empleado_entity(sector, cargo, **overrides)
    await SqlAlchemyEmpleadoRepository(db).add(empleado)
    return empleado
