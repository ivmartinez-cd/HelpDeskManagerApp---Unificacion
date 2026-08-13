from datetime import date

from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.repositories.asignacion_override_repository import (
    AsignacionOverrideRepository,
)
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)
from src.modules.contadores.domain.services.operador_efectivo import resolver_operador_efectivo


class GetCalendarEventsUseCase:
    """Lee la copia local (sincronizada aparte, ver SyncCalendarEventsUseCase).
    Superadmin ve todos los operadores por default, y puede filtrar por uno
    puntual vía `request.operador_id` — sin resolución de overrides, es una
    vista administrativa de la asignación cruda. El resto ve solo lo que
    matchea su propio full_name contra el catálogo de operadores de Gestión,
    con overrides activos ya aplicados (ver ADR-013): pierde los eventos
    propios que un override le reasignó a otro, y gana los eventos de
    cualquier operador que esté cubriendo — sin match de operador, no ve
    eventos (no hay a qué operador filtrar), y no puede pedir el operador de
    otra persona vía el filtro."""

    def __init__(
        self, repository: CalendarEventRepository, overrides: AsignacionOverrideRepository
    ) -> None:
        self._repository = repository
        self._overrides = overrides

    async def execute(self, request: GetCalendarEventsRequest) -> list[CalendarEvent]:
        if request.is_superadmin:
            return await self._repository.list_events(
                start_date=request.start_date,
                end_date=request.end_date,
                operador_id=request.operador_id,
            )

        operador = await self._repository.find_operador_by_nombre(request.full_name)
        if operador is None:
            return []

        propios = await self._propios_no_cubiertos(operador.id, request)
        cubiertos = await self._eventos_cubiertos(operador.id, request)
        return _dedupe_by_id(propios + cubiertos)

    async def _propios_no_cubiertos(
        self, operador_id: str, request: GetCalendarEventsRequest
    ) -> list[CalendarEvent]:
        eventos = await self._repository.list_events(
            start_date=request.start_date, end_date=request.end_date, operador_id=operador_id
        )
        overrides_donde_soy_ausente = await self._overrides.list_activos_por_ausente(operador_id)
        return [
            e
            for e in eventos
            if resolver_operador_efectivo(
                operador_id, e.cliente, _event_date(e), overrides_donde_soy_ausente
            )
            == operador_id
        ]

    async def _eventos_cubiertos(
        self, operador_id: str, request: GetCalendarEventsRequest
    ) -> list[CalendarEvent]:
        cubro_a = await self._overrides.list_activos_por_reemplazante(operador_id)
        cubiertos: list[CalendarEvent] = []
        for ausente_id in {o.operador_ausente_id for o in cubro_a}:
            reglas = [o for o in cubro_a if o.operador_ausente_id == ausente_id]
            eventos = await self._repository.list_events(
                start_date=request.start_date, end_date=request.end_date, operador_id=ausente_id
            )
            cubiertos += [
                e
                for e in eventos
                if resolver_operador_efectivo(ausente_id, e.cliente, _event_date(e), reglas)
                == operador_id
            ]
        return cubiertos


def _event_date(event: CalendarEvent) -> date:
    return date.fromisoformat(event.start[:10])


def _dedupe_by_id(events: list[CalendarEvent]) -> list[CalendarEvent]:
    seen: set[str] = set()
    deduped: list[CalendarEvent] = []
    for event in events:
        if event.id in seen:
            continue
        seen.add(event.id)
        deduped.append(event)
    return deduped
