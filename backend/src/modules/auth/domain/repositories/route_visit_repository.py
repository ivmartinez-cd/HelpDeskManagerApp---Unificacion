from datetime import date
from typing import Protocol
from uuid import UUID

from src.modules.auth.domain.entities.route_visit_count import RouteVisitCount


class RouteVisitRepository(Protocol):
    async def increment(
        self, *, user_id: UUID, route: str, day: date, max_routes_per_day: int
    ) -> None: ...

    async def purge_before(self, *, user_id: UUID, cutoff: date) -> None: ...

    async def top_routes(
        self, *, user_id: UUID, since: date, limit: int
    ) -> list[RouteVisitCount]: ...
