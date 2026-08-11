from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)


class GetCalendarEventsUseCase:
    """Lee la copia local (sincronizada aparte, ver SyncCalendarEventsUseCase).
    Superadmin ve todos los operadores por default, y puede filtrar por uno
    puntual vía `request.operador_id`; el resto ve solo lo que matchea su
    propio full_name contra el catálogo de operadores de Gestión — sin match,
    no ve eventos (no hay a qué operador filtrar), y no puede pedir el
    operador de otra persona vía el filtro."""

    def __init__(self, repository: CalendarEventRepository) -> None:
        self._repository = repository

    async def execute(self, request: GetCalendarEventsRequest) -> list[CalendarEvent]:
        if request.is_superadmin:
            operador_id = request.operador_id
        else:
            operador = await self._repository.find_operador_by_nombre(request.full_name)
            if operador is None:
                return []
            operador_id = operador.id

        return await self._repository.list_events(
            start_date=request.start_date,
            end_date=request.end_date,
            operador_id=operador_id,
        )
