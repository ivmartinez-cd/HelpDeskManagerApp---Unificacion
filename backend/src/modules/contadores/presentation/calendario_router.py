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
from src.modules.contadores.presentation.schemas.calendario_schemas import (
    CalendarEventSchema,
    GetCalendarEventsResponse,
)

router = APIRouter(prefix="/api/contadores", tags=["contadores-calendario"])

_require_view = Depends(require_permission(VIEW))


@router.get("/calendario")
async def get_calendario_events(
    start: str = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end: str = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    operador_id: str | None = Query(None, description="ID del operador en gestión"),
    tipo_evento: list[str] | None = Query(None, description="Tipos de eventos a filtrar"),
    solo_facturacion: bool = Query(True, description="Filtrar solo eventos de Facturación"),
    _: Identity = _require_view,
) -> GetCalendarEventsResponse:
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
    return GetCalendarEventsResponse(events=schema_events, total=len(schema_events))

