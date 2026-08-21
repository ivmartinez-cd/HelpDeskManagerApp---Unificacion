import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.features import require_feature
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.vacaciones.application.use_cases.actualizar_config import (
    ActualizarConfig,
    ActualizarConfigDependencies,
)
from src.modules.vacaciones.application.use_cases.gestionar_ciclos import (
    AbrirCiclosProximoAnio,
    CiclosDependencies,
    ListarCiclos,
    ObtenerSaldoEmpleado,
)
from src.modules.vacaciones.application.use_cases.gestionar_exclusiones import (
    CrearExclusion,
    EliminarExclusion,
    ExclusionesDependencies,
    ListarExclusiones,
)
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.modules.vacaciones.domain.well_known_features import CONFIGURACION
from src.modules.vacaciones.domain.well_known_permissions import MANAGE, VIEW
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_auditoria import (
    SqlAlchemyRegistradorAuditoria,
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
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_solicitud_repository import (  # noqa: E501
    SqlAlchemySolicitudRepository,
)
from src.modules.vacaciones.infrastructure.system_clock import SystemClock
from src.modules.vacaciones.presentation.dependencies.actor import get_actor_vacaciones
from src.modules.vacaciones.presentation.schemas.config_schemas import (
    ConfigResponse,
    ConfigUpdateRequest,
    ExclusionRequest,
    ExclusionResponse,
)
from src.modules.vacaciones.presentation.schemas.dashboard_schemas import (
    AbrirCiclosResponse,
    CicloResponse,
    SaldoResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/vacaciones", tags=["vacaciones"])

_DEFAULT_SIZE = 200
_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))
# Pantalla Configuración: función concedible por usuario (ADR-032).
_require_config = Depends(require_feature(CONFIGURACION))


def _ciclos_deps(db: AsyncSession) -> CiclosDependencies:
    return CiclosDependencies(
        ciclos=SqlAlchemyCicloRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
        solicitudes=SqlAlchemySolicitudRepository(db),
        config=SqlAlchemyConfigRepository(db),
        clock=SystemClock(),
    )


def _exclusiones_deps(db: AsyncSession) -> ExclusionesDependencies:
    return ExclusionesDependencies(
        exclusiones=SqlAlchemyExclusionRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
    )


@router.get("/ciclos")
async def list_ciclos(
    year: int = Query(),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[CicloResponse]:
    dtos = await ListarCiclos(_ciclos_deps(db)).execute(year)
    return Page.of([CicloResponse.from_dto(d) for d in dtos], page=page, size=size)


@router.post("/ciclos/abrir-proximo")
async def abrir_ciclos_proximo(
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AbrirCiclosResponse:
    resultado = await AbrirCiclosProximoAnio(_ciclos_deps(db)).execute()
    return AbrirCiclosResponse.from_dto(resultado)


@router.get("/ciclos/empleado/{empleado_id}")
async def saldo_empleado(
    empleado_id: uuid.UUID,
    year: int | None = Query(default=None),
    _identity: Identity = _require_view,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SaldoResponse:
    target = year if year is not None else SystemClock().hoy().year
    saldo = await ObtenerSaldoEmpleado(_ciclos_deps(db)).execute(empleado_id, target, actor)
    return SaldoResponse.from_saldo(saldo)


@router.get("/config")
async def get_config(
    _identity: Identity = _require_config,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ConfigResponse:
    config = await SqlAlchemyConfigRepository(db).get()
    return ConfigResponse.from_config(config)


@router.put("/config")
async def update_config(
    body: ConfigUpdateRequest,
    identity: Identity = _require_config,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ConfigResponse:
    deps = ActualizarConfigDependencies(
        config=SqlAlchemyConfigRepository(db),
        auditoria=SqlAlchemyRegistradorAuditoria(db, identity.user.id),
    )
    config = await ActualizarConfig(deps).execute(body.to_command())
    return ConfigResponse.from_config(config)


@router.get("/exclusiones")
async def list_exclusiones(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=500),
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[ExclusionResponse]:
    dtos = await ListarExclusiones(_exclusiones_deps(db)).execute()
    return Page.of([ExclusionResponse.from_dto(d) for d in dtos], page=page, size=size)


@router.post("/exclusiones", status_code=status.HTTP_201_CREATED)
async def crear_exclusion(
    body: ExclusionRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> dict[str, uuid.UUID]:
    exclusion = await CrearExclusion(_exclusiones_deps(db)).execute(
        body.empleado_a_id, body.empleado_b_id
    )
    return {"id": exclusion.id}


@router.delete("/exclusiones/{exclusion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_exclusion(
    exclusion_id: uuid.UUID,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    await EliminarExclusion(_exclusiones_deps(db)).execute(exclusion_id)
