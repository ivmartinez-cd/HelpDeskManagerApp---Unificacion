import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.vacaciones.application.dtos.gestion_dtos import ListEmpleadosQuery
from src.modules.vacaciones.application.use_cases.gestionar_empleados import (
    CreateEmpleado,
    DeleteEmpleado,
    GestionEmpleadosDependencies,
    ListEmpleados,
    UpdateEmpleado,
)
from src.modules.vacaciones.domain.entities.empleado import EstadoEmpleado
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.modules.vacaciones.domain.well_known_permissions import MANAGE, VIEW
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_cargo_repository import (
    SqlAlchemyCargoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_ciclo_repository import (
    SqlAlchemyCicloRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_config_repository import (
    SqlAlchemyConfigRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_sector_repository import (
    SqlAlchemySectorRepository,
)
from src.modules.vacaciones.infrastructure.system_clock import SystemClock
from src.modules.vacaciones.presentation.dependencies.actor import get_actor_vacaciones
from src.modules.vacaciones.presentation.schemas.empleado_schemas import (
    EmpleadoListItemResponse,
    EmpleadoRequest,
    EmpleadoResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/vacaciones/empleados", tags=["vacaciones"])

# Catálogo chico (decenas de empleados): paginado por contrato con default
# generoso — alimenta la tabla completa de Gestión Humana.
_DEFAULT_SIZE = 200
_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))


def _deps(db: AsyncSession) -> GestionEmpleadosDependencies:
    return GestionEmpleadosDependencies(
        empleados=SqlAlchemyEmpleadoRepository(db),
        sectores=SqlAlchemySectorRepository(db),
        cargos=SqlAlchemyCargoRepository(db),
        ciclos=SqlAlchemyCicloRepository(db),
        config=SqlAlchemyConfigRepository(db),
        clock=SystemClock(),
    )


@router.get("")
async def list_empleados(
    search: str | None = Query(default=None),
    department_id: uuid.UUID | None = Query(default=None, alias="departmentId"),
    estado: EstadoEmpleado | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = _require_view,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db),
) -> Page[EmpleadoListItemResponse]:
    query = ListEmpleadosQuery(search=search, department_id=department_id, status=estado)
    items = await ListEmpleados(_deps(db)).execute(query, actor)
    return Page.of(
        [EmpleadoListItemResponse.from_dto(i) for i in items], page=page, size=size
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_empleado(
    body: EmpleadoRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> EmpleadoResponse:
    empleado = await CreateEmpleado(_deps(db)).execute(body.to_command())
    return EmpleadoResponse.from_entity(empleado)


@router.put("/{empleado_id}")
async def update_empleado(
    empleado_id: uuid.UUID,
    body: EmpleadoRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> EmpleadoResponse:
    empleado = await UpdateEmpleado(_deps(db)).execute(empleado_id, body.to_command())
    return EmpleadoResponse.from_entity(empleado)


@router.delete("/{empleado_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_empleado(
    empleado_id: uuid.UUID,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> None:
    await DeleteEmpleado(_deps(db)).execute(empleado_id)
