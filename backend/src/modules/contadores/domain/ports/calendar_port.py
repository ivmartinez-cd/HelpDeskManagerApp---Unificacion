from typing import Protocol

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent


class CalendarPort(Protocol):
    """Puerto de dominio para la recuperación de eventos del calendario."""

    async def get_events(
        self,
        start_date: str,
        end_date: str,
        operador_id: str | None = None,
        tipo_evento: list[str] | None = None,
        solo_facturacion: bool = True,
    ) -> list[CalendarEvent]: ...

