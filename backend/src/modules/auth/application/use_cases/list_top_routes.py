from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from src.modules.auth.domain.entities.route_visit_count import RouteVisitCount
from src.modules.auth.domain.repositories.route_visit_repository import RouteVisitRepository

_WINDOW_DAYS = 30


@dataclass(frozen=True, slots=True)
class ListTopRoutesDependencies:
    visits: RouteVisitRepository
    timezone: str


class ListTopRoutes:
    """Ranking personal de accesos directos (ADR-028): las rutas más
    visitadas por el usuario logueado en los últimos 30 días, para
    completar la fila de accesos directos de Inicio."""

    def __init__(self, deps: ListTopRoutesDependencies) -> None:
        self._deps = deps

    async def execute(self, *, user_id: UUID, limit: int) -> list[RouteVisitCount]:
        today = datetime.now(ZoneInfo(self._deps.timezone)).date()
        since = today - timedelta(days=_WINDOW_DAYS)
        return await self._deps.visits.top_routes(user_id=user_id, since=since, limit=limit)
