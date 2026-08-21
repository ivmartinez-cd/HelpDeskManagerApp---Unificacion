from datetime import date
from uuid import UUID

from sqlalchemy import ColumnElement, Date, String, and_, delete, func, literal, or_, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.route_visit_count import RouteVisitCount
from src.modules.auth.infrastructure.models.route_visit_model import UserRouteVisit

_PK = [UserRouteVisit.user_id, UserRouteVisit.visit_date, UserRouteVisit.route]


class SqlAlchemyRouteVisitRepository:
    """Sin commit: el límite transaccional vive en `get_db` (una sola vez
    por request, ver shared/infrastructure/database/session.py)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def increment(
        self, *, user_id: UUID, route: str, day: date, max_routes_per_day: int
    ) -> None:
        source = select(
            literal(user_id, type_=postgresql.UUID(as_uuid=True)).label("user_id"),
            literal(day, type_=Date).label("visit_date"),
            literal(route, type_=String(128)).label("route"),
        ).where(_within_daily_cap(user_id, day, route, max_routes_per_day))
        stmt = pg_insert(UserRouteVisit).from_select(["user_id", "visit_date", "route"], source)
        # `stmt.excluded.visit_count` sería el valor propuesto (1), no el
        # acumulado -- hay que sumarle a la columna de la fila existente.
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=_PK, set_={"visit_count": UserRouteVisit.visit_count + 1}
            )
        )

    async def purge_before(self, *, user_id: UUID, cutoff: date) -> None:
        await self._session.execute(
            delete(UserRouteVisit).where(
                UserRouteVisit.user_id == user_id, UserRouteVisit.visit_date < cutoff
            )
        )

    async def top_routes(self, *, user_id: UUID, since: date, limit: int) -> list[RouteVisitCount]:
        total = func.sum(UserRouteVisit.visit_count).label("total")
        ultima = func.max(UserRouteVisit.visit_date).label("last_visit")
        stmt = (
            select(UserRouteVisit.route, total, ultima)
            .where(UserRouteVisit.user_id == user_id, UserRouteVisit.visit_date >= since)
            .group_by(UserRouteVisit.route)
            # Desempate explícito: sin orden total, un empate de conteo
            # reordenaría la fila de accesos directos entre requests.
            .order_by(total.desc(), ultima.desc(), UserRouteVisit.route.asc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            RouteVisitCount(route=r.route, visits=int(r.total), last_visit=r.last_visit)
            for r in rows
        ]


def _within_daily_cap(user_id: UUID, day: date, route: str, cap: int) -> ColumnElement[bool]:
    """Techo de rutas DISTINTAS por usuario y día. La rama `ya_existe` es la
    que importa: sin ella, al tocar el techo se congelaría también el
    conteo de las rutas legítimas ya registradas ese día."""
    del_dia = and_(UserRouteVisit.user_id == user_id, UserRouteVisit.visit_date == day)
    distintas = select(func.count()).select_from(UserRouteVisit).where(del_dia).scalar_subquery()
    ya_existe = select(literal(1)).where(del_dia, UserRouteVisit.route == route).exists()
    return or_(distintas < cap, ya_existe)
