import logging
from collections import Counter, defaultdict
from datetime import UTC, datetime

from src.modules.contadores.application.dtos.sync_calendar_events_result import (
    SyncCalendarEventsResult,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.domain.ports.calendar_port import CalendarPort
from src.modules.contadores.domain.ports.operador_catalog_port import OperadorCatalogPort
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)

logger = logging.getLogger(__name__)


class SyncCalendarEventsUseCase:
    """Reconstruye la copia local de eventos de facturación con UN solo pedido
    sin filtro de operador: ajax-by-rango ya trae el username del operador en
    cada evento de facturación (campo `operador`), así que pedir el rango una
    vez por operador —como se hacía antes— multiplicaba por ~50 los requests
    a Gestión y moría por timeout. El username es la identidad local del
    operador; su nombre real se resuelve contra Siges/UsuariosWeb
    (OperadorCatalogPort, ver ADR-012). El color, en cambio, sale del color
    dominante de los propios eventos del operador: `UsuariosWeb.color` está
    desactualizado/duplicado (verificado 2026-08-14: ltorres figura #BC2FFE
    igual que mjvela, pero sus eventos en Gestión son #FFC0CB — el color que
    la gente reconoce en el calendario); UsuariosWeb queda solo como fallback
    para un operador cuyos eventos no traigan color. Full replace del rango:
    los cambios de operador o de clientes en Gestión se reflejan sin dejar
    basura vieja, y un operador sin eventos en toda la ventana se poda.
    """

    def __init__(
        self,
        calendar_port: CalendarPort,
        operador_catalog: OperadorCatalogPort,
        repository: CalendarEventRepository,
    ) -> None:
        self._calendar_port = calendar_port
        self._operador_catalog = operador_catalog
        self._repository = repository

    async def execute(self, *, start_date: str, end_date: str) -> SyncCalendarEventsResult:
        fetched = await self._calendar_port.get_events(
            start_date=start_date, end_date=end_date, solo_facturacion=True
        )
        events = _drop_events_sin_operador(fetched)
        por_operador = _group_by_operador(events)
        identidades = await self._operador_catalog.find_by_logins(sorted(por_operador))
        operadores = _build_operadores(por_operador, identidades)

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


def _build_operadores(
    por_operador: dict[str, list[CalendarEvent]], identidades: list[Operador]
) -> list[Operador]:
    por_login = {op.id: op for op in identidades}
    operadores: list[Operador] = []
    for username in sorted(por_operador):
        identidad = por_login.get(username)
        if identidad is None:
            logger.warning(
                "Operador sin identidad resuelta en Siges/UsuariosWeb, se usa el username",
                extra={"username": username},
            )
        color = _color_dominante(por_operador[username]) or (
            identidad.color if identidad else None
        )
        nombre = identidad.nombre if identidad else username
        operadores.append(Operador(id=username, nombre=nombre, color=color))
    return operadores


def _color_dominante(events: list[CalendarEvent]) -> str | None:
    """El color con que Gestión pinta los eventos del operador — su identidad
    visual real en el calendario (ver docstring del use case)."""
    conteo = Counter(e.background_color for e in events if e.background_color)
    return conteo.most_common(1)[0][0] if conteo else None
