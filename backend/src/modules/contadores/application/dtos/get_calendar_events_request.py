from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GetCalendarEventsRequest:
    """El Calendario siempre lee de la copia local sincronizada. Para un
    usuario regular el operador no es un query param libre: se resuelve solo
    a partir de quién inició sesión. Superadmin sí puede filtrar por
    cualquier operador vía `operador_id` (o dejarlo en None para ver todos)
    — ver GetCalendarEventsUseCase."""

    start_date: str
    end_date: str
    is_superadmin: bool
    full_name: str
    operador_id: str | None = None

