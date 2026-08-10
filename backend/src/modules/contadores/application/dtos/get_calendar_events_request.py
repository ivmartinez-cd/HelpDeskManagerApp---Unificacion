from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GetCalendarEventsRequest:
    start_date: str
    end_date: str
    operador_id: str | None = None
    tipo_evento: list[str] | None = None
    solo_facturacion: bool = True

