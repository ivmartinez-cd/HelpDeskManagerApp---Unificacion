from datetime import date, timedelta

from src.modules.contadores.application.dtos.calendar_event_anotado import CalendarEventAnotado
from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)


class GetPendingClientsUseCase:
    """Backlog de clientes pendientes para la card de Inicio. Un evento con
    fecha anterior a hoy que TODAVÍA está en el calendario es un cliente que
    quedó de arrastre (Gestión saca del calendario al que ya se realizó — es
    la única señal disponible, CalendarEvent no tiene estado). Reusa la
    visibilidad de GetCalendarEventsUseCase (operador propio + coberturas):
    un usuario nunca ve pendientes de otro operador. El rango excluye hoy
    (los clientes de hoy los trae otra llamada) y arranca `cutoff_days` atrás.
    Ordena del más viejo al más nuevo para que el mayor atraso quede arriba."""

    def __init__(self, events: GetCalendarEventsUseCase) -> None:
        self._events = events

    async def execute(
        self, *, is_superadmin: bool, full_name: str, today: date, cutoff_days: int
    ) -> list[CalendarEventAnotado]:
        start = (today - timedelta(days=cutoff_days)).isoformat()
        end = (today - timedelta(days=1)).isoformat()
        anotados = await self._events.execute(
            GetCalendarEventsRequest(
                start_date=start,
                end_date=end,
                is_superadmin=is_superadmin,
                full_name=full_name,
                operador_id=None,
            )
        )
        return sorted(anotados, key=lambda anotado: anotado.event.start)
