from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class RouteVisitCount:
    """Ranking agregado: cuántas veces (`visits`) visitó `route` el usuario
    en la ventana consultada, y cuándo fue la última vez."""

    route: str
    visits: int
    last_visit: date
