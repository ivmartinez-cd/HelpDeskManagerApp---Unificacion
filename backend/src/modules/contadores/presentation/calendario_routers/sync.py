"""Sync del calendario contra Gestión: estado y disparo manual."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.contadores.application.use_cases.sync_calendar_events import (
    SyncCalendarEventsUseCase,
)
from src.modules.contadores.infrastructure.gestion.gestion_planificacion_client import (
    GestionPlanificacionClient,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)
from src.modules.contadores.presentation.calendario_routers._deps import (
    DEFAULT_SYNC_WINDOW_DAYS,
    SYNC_TIMEOUT_SECONDS,
    require_manage,
    require_view,
)
from src.modules.contadores.presentation.dependencies import get_operador_catalog_gateway
from src.modules.contadores.presentation.schemas.calendario_schemas import (
    SyncCalendarioResponse,
    SyncStatusResponse,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter()


@router.get("/calendario/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    repo = SqlAlchemyCalendarEventRepository(db)
    last_synced_at = await repo.last_synced_at()
    total_events = await repo.count_events()
    return SyncStatusResponse(last_synced_at=last_synced_at, total_events=total_events)


@router.post("/calendario/sync", response_model=SyncCalendarioResponse)
async def sync_calendario(
    _: Identity = require_manage,
    db: AsyncSession = Depends(get_db),
) -> SyncCalendarioResponse:
    today = datetime.now(UTC).date()
    window = timedelta(days=DEFAULT_SYNC_WINDOW_DAYS)
    start_date = (today - window).isoformat()
    end_date = (today + window).isoformat()

    repo = SqlAlchemyCalendarEventRepository(db)
    gestion = GestionPlanificacionClient(timeout=SYNC_TIMEOUT_SECONDS)
    operador_catalog = get_operador_catalog_gateway()
    use_case = SyncCalendarEventsUseCase(gestion, operador_catalog, repo)
    result = await use_case.execute(start_date=start_date, end_date=end_date)
    return SyncCalendarioResponse.model_validate(result)
