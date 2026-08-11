from fastapi import APIRouter, Depends, Query

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.domain.well_known_permissions import VIEW
from src.modules.contadores.infrastructure.gestion.gestion_planificacion_client import (
    GestionPlanificacionClient,
)
from src.modules.contadores.presentation.schemas.calendario_schemas import CalendarEventSchema
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/contadores", tags=["contadores-calendario"])

_require_view = Depends(require_permission(VIEW))
# Un mes con muchos eventos de facturación no debería superar esto; si algún
# rango lo hace, subir el tope antes que silenciar la paginación.
_MAX_PAGE_SIZE = 2000


@router.get("/calendario", response_model=Page[CalendarEventSchema])
async def get_calendario_events(
    start: str = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end: str = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    operador_id: str | None = Query(None, description="ID del operador en gestión"),
    tipo_evento: list[str] | None = Query(None, description="Tipos de eventos a filtrar"),
    solo_facturacion: bool = Query(True, description="Filtrar solo eventos de Facturación"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_view,
) -> Page[CalendarEventSchema]:
    use_case = GetCalendarEventsUseCase(GestionPlanificacionClient())
    request = GetCalendarEventsRequest(
        start_date=start,
        end_date=end,
        operador_id=operador_id,
        tipo_evento=tipo_evento,
        solo_facturacion=solo_facturacion,
    )
    events = await use_case.execute(request)
    schema_events = [CalendarEventSchema.model_validate(e) for e in events]
    return Page.of(schema_events, page=page, size=size)

