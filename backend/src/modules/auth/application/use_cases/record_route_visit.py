from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from src.modules.auth.domain.errors import UnknownRouteError
from src.modules.auth.domain.repositories.module_catalog_repository import (
    ModuleCatalogRepository,
)
from src.modules.auth.domain.repositories.route_visit_repository import RouteVisitRepository
from src.modules.auth.domain.value_objects.route_path import RoutePath
from src.shared.domain.value_objects.module_key import ModuleKey

# Techo de rutas DISTINTAS por usuario y día — acota el crecimiento de la
# tabla sin necesitar rate limiting HTTP (app interna detrás de sesión).
_MAX_ROUTES_PER_DAY = 60
# Retención: purgada inline en cada POST, sin job de fondo aparte.
_RETENTION_DAYS = 90


@dataclass(frozen=True, slots=True)
class RecordRouteVisitDependencies:
    visits: RouteVisitRepository
    catalog: ModuleCatalogRepository
    timezone: str


class RecordRouteVisit:
    """Incrementa el contador de visitas de hoy para (usuario, ruta) — ADR-028.

    `raw_route` valida forma (RoutePath) y que el primer segmento sea un
    módulo habilitado del catálogo. El frontend solo postea su propia
    whitelist, así que una ruta rechazada acá es señal de bug, no de un
    usuario malicioso: por eso lanza en vez de descartar en silencio."""

    def __init__(self, deps: RecordRouteVisitDependencies) -> None:
        self._deps = deps

    async def execute(self, *, user_id: UUID, raw_route: str) -> None:
        route = RoutePath(raw_route)
        if not await self._deps.catalog.is_enabled(ModuleKey(route.module_key)):
            raise UnknownRouteError(raw_route)
        today = datetime.now(ZoneInfo(self._deps.timezone)).date()
        await self._deps.visits.increment(
            user_id=user_id,
            route=route.value,
            day=today,
            max_routes_per_day=_MAX_ROUTES_PER_DAY,
        )
        await self._deps.visits.purge_before(
            user_id=user_id, cutoff=today - timedelta(days=_RETENTION_DAYS)
        )
