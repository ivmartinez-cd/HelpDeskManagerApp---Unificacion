from datetime import date, timedelta

from src.modules.contadores.application.dtos.calendar_event_anotado import CalendarEventAnotado
from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)


class GetPendingClientsUseCase:
    """Backlog de clientes pendientes para la card de Inicio. Un evento con
    fecha anterior a hoy que TODAVÍA está en el calendario es un cliente que
    quedó de arrastre (Gestión saca del calendario al que ya se realizó — es
    la única señal disponible, CalendarEvent no tiene estado). Solo se
    incluyen eventos asignados al operador propio del usuario — los eventos de
    operadores que el usuario cubre por override NO aparecen en el backlog:
    el arrastre es responsabilidad del operador original, no del reemplazante.
    Los operadores pool configurados en `exclude_operador_ids` se omiten
    siempre (cuentas de Gestión sin persona real detrás). El superadmin ve
    todos los operadores no excluidos."""

    def __init__(
        self, events: GetCalendarEventsUseCase, repository: CalendarEventRepository
    ) -> None:
        self._events = events
        self._repository = repository

    async def execute(
        self,
        *,
        is_superadmin: bool,
        full_name: str,
        today: date,
        cutoff_days: int,
        exclude_operador_ids: frozenset[str] = frozenset(),
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
        if not is_superadmin:
            anotados = await self._filter_solo_propios(anotados, full_name)
        if exclude_operador_ids:
            anotados = [a for a in anotados if a.event.operador_id not in exclude_operador_ids]
        return sorted(anotados, key=lambda anotado: anotado.event.start)

    async def _filter_solo_propios(
        self, anotados: list[CalendarEventAnotado], full_name: str
    ) -> list[CalendarEventAnotado]:
        operador = await self._repository.find_operador_by_nombre(full_name)
        if operador is None:
            return []
        return [a for a in anotados if a.event.operador_id == operador.id]
