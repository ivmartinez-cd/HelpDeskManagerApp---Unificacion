from datetime import datetime
from typing import Protocol

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador


class CalendarEventRepository(Protocol):
    """Persistencia local de eventos de facturación y catálogo de operadores
    sincronizados desde Gestión — el Calendario lee siempre de acá, nunca en
    vivo (ver SyncCalendarEventsUseCase para la sincronización)."""

    async def list_events(
        self, *, start_date: str, end_date: str, operador_id: str | None
    ) -> list[CalendarEvent]: ...

    async def replace_events_in_range(
        self, *, start_date: str, end_date: str, events: list[CalendarEvent]
    ) -> None: ...

    async def prune_operadores_not_in(self, operador_ids: list[str]) -> None: ...

    async def list_operadores(self) -> list[Operador]: ...

    async def replace_operadores(self, operadores: list[Operador]) -> None: ...

    async def find_operador_by_nombre(self, nombre: str) -> Operador | None: ...

    async def last_synced_at(self) -> datetime | None: ...

    async def count_events(self) -> int: ...
