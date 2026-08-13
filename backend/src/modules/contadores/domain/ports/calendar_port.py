from typing import Protocol

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent


class CalendarPort(Protocol):
    """Puerto de dominio para la recuperación de eventos del calendario de
    planificación, en vivo desde Gestión. La identidad de los operadores
    (nombre/color) ya no se resuelve contra Gestión — ver OperadorCatalogPort
    y ADR-012."""

    async def get_events(
        self,
        start_date: str,
        end_date: str,
        operador_id: str | None = None,
        tipo_evento: list[str] | None = None,
        solo_facturacion: bool = True,
    ) -> list[CalendarEvent]: ...

