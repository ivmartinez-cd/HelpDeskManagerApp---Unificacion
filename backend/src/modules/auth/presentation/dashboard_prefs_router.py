from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.use_cases.dashboard_prefs import (
    GetDashboardPrefs,
    SaveDashboardPrefs,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_dashboard_prefs_repository import (
    SqlAlchemyDashboardPrefsRepository,
)
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.auth.presentation.schemas.dashboard_prefs_schemas import (
    DashboardPrefsBody,
    DashboardPrefsResponse,
)
from src.shared.infrastructure.database.session import get_db

# /api/me/...: recurso del propio usuario logueado, gateado solo por sesión
# (misma decisión que /api/me/route-visits, ADR-028; ver ADR-033). El
# `user_id` sale siempre de la identidad, nunca del body ni de la URL.
router = APIRouter(prefix="/api/me/inicio-prefs", tags=["me"])


@router.get("")
async def get_prefs(
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> DashboardPrefsResponse:
    prefs = await GetDashboardPrefs(SqlAlchemyDashboardPrefsRepository(db)).execute(
        identity.user.id
    )
    return DashboardPrefsResponse.from_domain(prefs)


@router.put("")
async def put_prefs(
    payload: DashboardPrefsBody,
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> DashboardPrefsResponse:
    prefs = await SaveDashboardPrefs(SqlAlchemyDashboardPrefsRepository(db)).execute(
        user_id=identity.user.id,
        hidden_cards=payload.hidden_cards,
        initial_view=payload.initial_view,
    )
    return DashboardPrefsResponse.from_domain(prefs)
