from typing import Protocol

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent


class CalendarPort(Protocol):
    """Puerto de dominio para los eventos de facturación del calendario de
    planificación de Gestión (los que el operador todavía no marcó como
    realizados). La identidad de los operadores (nombre/color) se resuelve
    aparte — ver OperadorCatalogPort, ADR-012 y ADR-047."""

    async def get_events(self, start_date: str, end_date: str) -> list[CalendarEvent]: ...
