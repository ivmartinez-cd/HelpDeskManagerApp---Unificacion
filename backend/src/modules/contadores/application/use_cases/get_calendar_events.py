from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.ports.calendar_port import CalendarPort


class GetCalendarEventsUseCase:
    """Caso de uso para obtener los eventos del calendario de planificación."""

    def __init__(self, calendar_port: CalendarPort) -> None:
        self._calendar_port = calendar_port

    async def execute(self, request: GetCalendarEventsRequest) -> list[CalendarEvent]:
        return await self._calendar_port.get_events(
            start_date=request.start_date,
            end_date=request.end_date,
            operador_id=request.operador_id,
            tipo_evento=request.tipo_evento,
            solo_facturacion=request.solo_facturacion,
        )

