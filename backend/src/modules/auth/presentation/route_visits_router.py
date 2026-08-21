from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.use_cases.list_top_routes import (
    ListTopRoutes,
    ListTopRoutesDependencies,
)
from src.modules.auth.application.use_cases.record_route_visit import (
    RecordRouteVisit,
    RecordRouteVisitDependencies,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_module_catalog_repository import (
    SqlAlchemyModuleCatalogRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_route_visit_repository import (
    SqlAlchemyRouteVisitRepository,
)
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.auth.presentation.schemas.route_visit_schemas import (
    RecordRouteVisitRequest,
    RouteVisitResponse,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

# /api/me/... (no /api/auth/...): el recurso es el propio usuario logueado,
# gateado solo por autenticación -- ver ADR-028 para el porqué de no sumar
# un permiso module/action nuevo acá.
router = APIRouter(prefix="/api/me/route-visits", tags=["me"])

_DEFAULT_TOP = 6


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def record_visit(
    payload: RecordRouteVisitRequest,
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    """Registra que el usuario logueado visitó `route` hoy. El `user_id`
    sale siempre de la sesión, nunca del body -- nadie puede escribir en
    nombre de otro usuario."""
    settings = get_settings()
    deps = RecordRouteVisitDependencies(
        visits=SqlAlchemyRouteVisitRepository(db),
        catalog=SqlAlchemyModuleCatalogRepository(db),
        timezone=settings.app_timezone,
    )
    await RecordRouteVisit(deps).execute(user_id=identity.user.id, raw_route=payload.route)


@router.get("/top")
async def top_visits(
    size: int = Query(default=_DEFAULT_TOP, ge=1, le=20),
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[RouteVisitResponse]:
    """Ranking personal de accesos directos (ventana de 30 días, ADR-028).
    `page` queda fijo en 1: es un ranking, no una colección navegable."""
    settings = get_settings()
    deps = ListTopRoutesDependencies(
        visits=SqlAlchemyRouteVisitRepository(db), timezone=settings.app_timezone
    )
    top = await ListTopRoutes(deps).execute(user_id=identity.user.id, limit=size)
    return Page.of([RouteVisitResponse.from_domain(entry) for entry in top], page=1, size=size)
