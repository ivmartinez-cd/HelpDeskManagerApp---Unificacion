import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.vacaciones.application.dtos.solicitud_dtos import ListarSolicitudesQuery
from src.modules.vacaciones.application.use_cases.decidir_solicitud import (
    DecidirSolicitud,
    DecidirSolicitudDependencies,
)
from src.modules.vacaciones.application.use_cases.gestionar_solicitudes import (
    CrearSolicitud,
    EditarSolicitud,
    EliminarSolicitud,
    SolicitudesDependencies,
)
from src.modules.vacaciones.application.use_cases.leer_solicitudes import (
    LeerSolicitudesDependencies,
    ListarSolapamientos,
    ListarSolicitudes,
    ObtenerSolicitud,
)
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.modules.vacaciones.domain.well_known_permissions import APPROVE, CREATE, VIEW
from src.modules.vacaciones.infrastructure.logging_notificador import LoggingNotificador
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_aprobacion_repository import (  # noqa: E501
    SqlAlchemyAprobacionRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_auditoria import (
    SqlAlchemyRegistradorAuditoria,
)
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
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_exclusion_repository import (  # noqa: E501
    SqlAlchemyExclusionRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_feriado_repository import (
    SqlAlchemyFeriadoRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_sector_repository import (
    SqlAlchemySectorRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_solicitud_repository import (  # noqa: E501
    SqlAlchemySolicitudRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_user_directory import (
    SqlAlchemyUserDirectory,
)
from src.modules.vacaciones.infrastructure.system_clock import SystemClock
from src.modules.vacaciones.presentation.dependencies.actor import get_actor_vacaciones
from src.modules.vacaciones.presentation.schemas.solicitud_schemas import (
    CrearSolicitudRequest,
    DecisionRequest,
    EditarSolicitudRequest,
    SolapamientosResponse,
    SolicitudResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/vacaciones/solicitudes", tags=["vacaciones"])

_DEFAULT_SIZE = 200
_require_view = Depends(require_permission(VIEW))
_require_create = Depends(require_permission(CREATE))
_require_approve = Depends(require_permission(APPROVE))


def _write_deps(db: AsyncSession, actor: ActorVacaciones) -> SolicitudesDependencies:
    return SolicitudesDependencies(
        solicitudes=SqlAlchemySolicitudRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
        sectores=SqlAlchemySectorRepository(db),
        cargos=SqlAlchemyCargoRepository(db),
        ciclos=SqlAlchemyCicloRepository(db),
        exclusiones=SqlAlchemyExclusionRepository(db),
        feriados=SqlAlchemyFeriadoRepository(db),
        config=SqlAlchemyConfigRepository(db),
        clock=SystemClock(),
        notificador=LoggingNotificador(),
        auditoria=SqlAlchemyRegistradorAuditoria(db, actor.user_id),
    )


def _read_deps(db: AsyncSession) -> LeerSolicitudesDependencies:
    return LeerSolicitudesDependencies(
        solicitudes=SqlAlchemySolicitudRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
        sectores=SqlAlchemySectorRepository(db),
        aprobaciones=SqlAlchemyAprobacionRepository(db),
        users=SqlAlchemyUserDirectory(db),
    )


async def _leer_una(
    db: AsyncSession, solicitud_id: uuid.UUID, actor: ActorVacaciones
) -> SolicitudResponse:
    dto = await ObtenerSolicitud(_read_deps(db)).execute(solicitud_id, actor)
    return SolicitudResponse.from_dto(dto)


@router.get("")
async def list_solicitudes(
    estado: EstadoSolicitud | None = Query(default=None, alias="status"),
    empleado_id: uuid.UUID | None = Query(default=None, alias="employeeId"),
    department_id: uuid.UUID | None = Query(default=None, alias="departmentId"),
    desde: date | None = Query(default=None, alias="from"),
    hasta: date | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = _require_view,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db),
) -> Page[SolicitudResponse]:
    query = ListarSolicitudesQuery(
        status=estado,
        empleado_id=empleado_id,
        department_id=department_id,
        desde=desde,
        hasta=hasta,
    )
    dtos = await ListarSolicitudes(_read_deps(db)).execute(query, actor)
    return Page.of([SolicitudResponse.from_dto(d) for d in dtos], page=page, size=size)


@router.get("/{solicitud_id}")
async def get_solicitud(
    solicitud_id: uuid.UUID,
    _identity: Identity = _require_view,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db),
) -> SolicitudResponse:
    return await _leer_una(db, solicitud_id, actor)


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_solicitud(
    body: CrearSolicitudRequest,
    _identity: Identity = _require_create,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db),
) -> SolicitudResponse:
    solicitud = await CrearSolicitud(_write_deps(db, actor)).execute(
        body.to_command(), actor
    )
    return await _leer_una(db, solicitud.id, actor)


@router.put("/{solicitud_id}")
async def editar_solicitud(
    solicitud_id: uuid.UUID,
    body: EditarSolicitudRequest,
    _identity: Identity = _require_create,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db),
) -> SolicitudResponse:
    await EditarSolicitud(_write_deps(db, actor)).execute(
        solicitud_id, body.to_command(), actor
    )
    return await _leer_una(db, solicitud_id, actor)


@router.delete("/{solicitud_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_solicitud(
    solicitud_id: uuid.UUID,
    _identity: Identity = _require_create,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db),
) -> None:
    await EliminarSolicitud(_write_deps(db, actor)).execute(solicitud_id, actor)


@router.post("/{solicitud_id}/decision")
async def decidir_solicitud(
    solicitud_id: uuid.UUID,
    body: DecisionRequest,
    _identity: Identity = _require_approve,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db),
) -> SolicitudResponse:
    deps = DecidirSolicitudDependencies(
        solicitudes=SqlAlchemySolicitudRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
        aprobaciones=SqlAlchemyAprobacionRepository(db),
        notificador=LoggingNotificador(),
        auditoria=SqlAlchemyRegistradorAuditoria(db, actor.user_id),
    )
    await DecidirSolicitud(deps).execute(solicitud_id, body.to_command(), actor)
    return await _leer_una(db, solicitud_id, actor)


@router.get("/{solicitud_id}/solapamientos")
async def solapamientos(
    solicitud_id: uuid.UUID,
    _identity: Identity = _require_approve,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db),
) -> SolapamientosResponse:
    dto = await ListarSolapamientos(_read_deps(db)).execute(solicitud_id, actor)
    return SolapamientosResponse.from_dto(dto)
