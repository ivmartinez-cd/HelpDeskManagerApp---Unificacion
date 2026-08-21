from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.vacaciones.application.use_cases.calendario_eventos import (
    CalendarioDependencies,
    CalendarioEventos,
)
from src.modules.vacaciones.application.use_cases.dashboard_resumen import (
    DashboardDependencies,
    DashboardResumen,
)
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.modules.vacaciones.domain.well_known_permissions import VIEW
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_ciclo_repository import (
    SqlAlchemyCicloRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_config_repository import (
    SqlAlchemyConfigRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
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
from src.modules.vacaciones.infrastructure.system_clock import SystemClock
from src.modules.vacaciones.presentation.dependencies.actor import get_actor_vacaciones
from src.modules.vacaciones.presentation.schemas.dashboard_schemas import (
    DashboardResumenResponse,
    EventoCalendarioResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/vacaciones", tags=["vacaciones"])

_DEFAULT_SIZE = 500
_require_view = Depends(require_permission(VIEW))


@router.get("/dashboard/resumen")
async def dashboard_resumen(
    _identity: Identity = _require_view,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> DashboardResumenResponse:
    deps = DashboardDependencies(
        empleados=SqlAlchemyEmpleadoRepository(db),
        solicitudes=SqlAlchemySolicitudRepository(db),
        sectores=SqlAlchemySectorRepository(db),
        ciclos=SqlAlchemyCicloRepository(db),
        config=SqlAlchemyConfigRepository(db),
        clock=SystemClock(),
    )
    dto = await DashboardResumen(deps).execute(actor)
    return DashboardResumenResponse.from_dto(dto)


@router.get("/calendario")
async def calendario(
    desde: date | None = Query(default=None, alias="from"),
    hasta: date | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _identity: Identity = _require_view,
    actor: ActorVacaciones = Depends(get_actor_vacaciones),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[EventoCalendarioResponse]:
    deps = CalendarioDependencies(
        solicitudes=SqlAlchemySolicitudRepository(db),
        empleados=SqlAlchemyEmpleadoRepository(db),
        sectores=SqlAlchemySectorRepository(db),
        feriados=SqlAlchemyFeriadoRepository(db),
        ciclos=SqlAlchemyCicloRepository(db),
        config=SqlAlchemyConfigRepository(db),
        clock=SystemClock(),
    )
    eventos = await CalendarioEventos(deps).execute(desde, hasta, actor)
    return Page.of(
        [EventoCalendarioResponse.from_dto(e) for e in eventos], page=page, size=size
    )
