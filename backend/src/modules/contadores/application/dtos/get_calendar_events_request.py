from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GetCalendarEventsRequest:
    """El Calendario siempre lee de la copia local sincronizada — el filtro
    por operador ya no es un query param libre, se resuelve solo a partir
    de quién inició sesión (ver GetCalendarEventsUseCase)."""

    start_date: str
    end_date: str
    is_superadmin: bool
    full_name: str

