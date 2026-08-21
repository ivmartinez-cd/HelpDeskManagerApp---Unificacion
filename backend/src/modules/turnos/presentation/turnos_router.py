from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.turnos.application.use_cases.get_current_shifts import (
    GetCurrentShifts,
    GetCurrentShiftsDependencies,
)
from src.modules.turnos.domain.well_known_permissions import VIEW
from src.modules.turnos.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_asignacion_repository import (
    SqlAlchemyAsignacionRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_ausencias_lookup import (
    SqlAlchemyAusenciasLookup,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_casilla_repository import (
    SqlAlchemyCasillaRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_grilla_variante_repository import (  # noqa: E501
    SqlAlchemyGrillaVarianteRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_slot_repository import (
    SqlAlchemySlotRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_user_provider import (
    SqlAlchemyUserProvider,
)
from src.modules.turnos.presentation.schemas.grilla_variante_schemas import (
    CurrentShiftsResponse,
    VarianteActivaResponse,
)
from src.modules.turnos.presentation.schemas.turno_schemas import (
    ResolvedShiftResponse,
    UserOptionResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/turnos", tags=["turnos"])

# Catálogos chicos -- paginados por contrato (CLAUDE.md §11) pero con default
# generoso porque alimentan la grilla del home/el panel de admin completo, no
# una tabla paginada.
_DEFAULT_SIZE = 200
# turnos.view para consultar (ADR-029). `/current` queda solo-sesión: es la
# card de Inicio de cada operador.
_require_view = Depends(require_permission(VIEW))


@router.get("/current")
async def get_current_shifts(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> CurrentShiftsResponse:
    deps = GetCurrentShiftsDependencies(
        casillas=SqlAlchemyCasillaRepository(db),
        slots=SqlAlchemySlotRepository(db),
        asignaciones=SqlAlchemyAsignacionRepository(db),
        users=SqlAlchemyUserProvider(db),
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
        variantes=SqlAlchemyGrillaVarianteRepository(db),
        ausencias=SqlAlchemyAusenciasLookup(db),
    )
    result = await GetCurrentShifts(deps).execute()
    paged = Page.of(
        [ResolvedShiftResponse.from_dto(s) for s in result.shifts], page=page, size=size
    )
    return CurrentShiftsResponse(
        items=paged.items,
        total=paged.total,
        page=paged.page,
        size=paged.size,
        variante_activa=(
            VarianteActivaResponse.from_dto(result.variante_activa)
            if result.variante_activa is not None
            else None
        ),
    )


@router.get("/users")
async def list_assignable_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[UserOptionResponse]:
    provider = SqlAlchemyUserProvider(db)
    users = await provider.list_all_active_users()
    return Page.of(
        [UserOptionResponse.from_info(u) for u in users], page=page, size=size
    )
