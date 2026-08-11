import logging
from collections import Counter, defaultdict
from datetime import UTC, datetime

from src.modules.contadores.application.dtos.sync_calendar_events_result import (
    SyncCalendarEventsResult,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.ports.calendar_port import CalendarPort
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)
from src.modules.contadores.domain.services.operador_matcher import resolve_nombre_operador

logger = logging.getLogger(__name__)


class SyncCalendarEventsUseCase:
    """Reconstruye la copia local de eventos de facturación con UN solo pedido
    sin filtro de operador: ajax-by-rango ya trae el username del operador en
    cada evento de facturación (campo `operador`), así que pedir el rango una
    vez por operador del catálogo —como se hacía antes— multiplicaba por ~50
    los requests a Gestión y moría por timeout. El username es la identidad
    local del operador; su nombre visible se resuelve contra el catálogo de
    /planificacion/ver (ver operador_matcher). Full replace del rango: los
    cambios de operador o de clientes en Gestión se reflejan sin dejar basura
    vieja, y un operador sin eventos en toda la ventana se poda."""

    def __init__(self, calendar_port: CalendarPort, repository: CalendarEventRepository) -> None:
        self._calendar_port = calendar_port
        self._repository = repository

    async def execute(self, *, start_date: str, end_date: str) -> SyncCalendarEventsResult:
        catalogo = await self._calendar_port.get_operadores()
        fetched = await self._calendar_port.get_events(
            start_date=start_date, end_date=end_date, solo_facturacion=True
        )
        events = _drop_events_sin_operador(fetched)
        por_operador = _group_by_operador(events)
        operadores = [
            _build_operador(username, evts, catalogo)
            for username, evts in sorted(por_operador.items())
        ]

        await self._repository.replace_events_in_range(
            start_date=start_date, end_date=end_date, events=events
        )
        await self._repository.replace_operadores(operadores)
        await self._repository.prune_operadores_not_in([op.id for op in operadores])

        return SyncCalendarEventsResult(
            operadores_count=len(operadores),
            events_count=len(events),
            range_start=start_date,
            range_end=end_date,
            synced_at=datetime.now(UTC),
        )


def _drop_events_sin_operador(events: list[CalendarEvent]) -> list[CalendarEvent]:
    con_operador = [e for e in events if e.operador_id]
    descartados = len(events) - len(con_operador)
    if descartados:
        logger.warning(
            "Se descartaron eventos de facturación sin operador en la respuesta de Gestión",
            extra={"descartados": descartados, "total": len(events)},
        )
    return con_operador


def _group_by_operador(events: list[CalendarEvent]) -> dict[str, list[CalendarEvent]]:
    grouped: dict[str, list[CalendarEvent]] = defaultdict(list)
    for event in events:
        grouped[event.operador_id or ""].append(event)
    return grouped


def _build_operador(
    username: str, events: list[CalendarEvent], catalogo: list[Operador]
) -> Operador:
    nombre = resolve_nombre_operador(username, catalogo) or username
    return Operador(id=username, nombre=nombre, color=_most_common_color(events))


def _most_common_color(events: list[CalendarEvent]) -> str | None:
    colors = [e.background_color for e in events if e.background_color]
    if not colors:
        return None
    return Counter(colors).most_common(1)[0][0]
