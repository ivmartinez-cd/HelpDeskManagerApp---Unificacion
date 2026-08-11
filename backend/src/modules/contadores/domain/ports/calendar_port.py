from typing import Protocol

from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.operador import Operador


class CalendarPort(Protocol):
    """Puerto de dominio para la recuperación de eventos y operadores del
    calendario de planificación, en vivo desde Gestión."""

    async def get_events(
        self,
        start_date: str,
        end_date: str,
        operador_id: str | None = None,
        tipo_evento: list[str] | None = None,
        solo_facturacion: bool = True,
    ) -> list[CalendarEvent]: ...

    async def get_operadores(self) -> list[Operador]: ...

