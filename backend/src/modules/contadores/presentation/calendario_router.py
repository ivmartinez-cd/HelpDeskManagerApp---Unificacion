from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.application.use_cases.get_mi_operador import GetMiOperadorUseCase
from src.modules.contadores.application.use_cases.sync_calendar_events import (
    SyncCalendarEventsUseCase,
)
from src.modules.contadores.domain.well_known_permissions import MANAGE, VIEW
from src.modules.contadores.infrastructure.gestion.gestion_planificacion_client import (
    GestionPlanificacionClient,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)
from src.modules.contadores.presentation.schemas.calendario_schemas import (
    CalendarEventSchema,
    MiOperadorResponse,
    SyncCalendarioResponse,
    SyncStatusResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/contadores", tags=["contadores-calendario"])

_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))
# Un mes con muchos eventos de facturación no debería superar esto; si algún
# rango lo hace, subir el tope antes que silenciar la paginación.
_MAX_PAGE_SIZE = 2000
# Ventana por defecto de "Sincronizar": Gestión no entrega un diff, así que
# cada sync rehace este rango entero con UN pedido sin filtro (los eventos ya
# traen su operador — ver SyncCalendarEventsUseCase). ajax-by-rango se pone
# lento en rangos muy anchos — medido a mano: ~5s para 1 mes, ~20s para 180
# días, supera los 45s con más de un año. 90 días para cada lado cubre "todo
# lo vigente" quedando cómodo dentro del timeout.
_DEFAULT_SYNC_WINDOW_DAYS = 90
# Generoso a propósito: es una acción manual e infrecuente, no un fetch de
# página — 2.2x el tiempo medido del pedido de 180 días, con margen para los
# días en que Gestión anda lenta.
_SYNC_TIMEOUT_SECONDS = 45.0


@router.get("/calendario", response_model=Page[CalendarEventSchema])
async def get_calendario_events(
    start: str = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end: str = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=_MAX_PAGE_SIZE),
    identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[CalendarEventSchema]:
    repo = SqlAlchemyCalendarEventRepository(db)
    request = GetCalendarEventsRequest(
        start_date=start,
        end_date=end,
        is_superadmin=identity.user.is_superadmin,
        full_name=identity.user.full_name,
    )
    events = await GetCalendarEventsUseCase(repo).execute(request)
    schema_events = [CalendarEventSchema.model_validate(e) for e in events]
    return Page.of(schema_events, page=page, size=size)


@router.get("/calendario/mi-operador", response_model=MiOperadorResponse)
async def get_mi_operador(
    identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> MiOperadorResponse:
    repo = SqlAlchemyCalendarEventRepository(db)
    operador = await GetMiOperadorUseCase(repo).execute(
        is_superadmin=identity.user.is_superadmin, full_name=identity.user.full_name
    )
    if operador is None:
        return MiOperadorResponse(operador_id=None, nombre=None, color=None)
    return MiOperadorResponse(operador_id=operador.id, nombre=operador.nombre, color=operador.color)


@router.get("/calendario/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    repo = SqlAlchemyCalendarEventRepository(db)
    last_synced_at = await repo.last_synced_at()
    total_events = await repo.count_events()
    return SyncStatusResponse(last_synced_at=last_synced_at, total_events=total_events)


@router.post("/calendario/sync", response_model=SyncCalendarioResponse)
async def sync_calendario(
    _: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> SyncCalendarioResponse:
    today = datetime.now(UTC).date()
    window = timedelta(days=_DEFAULT_SYNC_WINDOW_DAYS)
    start_date = (today - window).isoformat()
    end_date = (today + window).isoformat()

    repo = SqlAlchemyCalendarEventRepository(db)
    gestion = GestionPlanificacionClient(timeout=_SYNC_TIMEOUT_SECONDS)
    use_case = SyncCalendarEventsUseCase(gestion, repo)
    result = await use_case.execute(start_date=start_date, end_date=end_date)
    return SyncCalendarioResponse.model_validate(result)
