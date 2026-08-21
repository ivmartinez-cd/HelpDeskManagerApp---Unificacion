import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from src.modules.auth.application.use_cases.list_top_routes import (
    ListTopRoutes,
    ListTopRoutesDependencies,
)
from src.modules.auth.application.use_cases.record_route_visit import (
    RecordRouteVisit,
    RecordRouteVisitDependencies,
)
from src.modules.auth.domain.errors import InvalidRoutePathError, UnknownRouteError
from tests.unit.application.auth.fakes import (
    FakeModuleCatalogRepository,
    FakeRouteVisitRepository,
)

_TZ = "America/Argentina/Buenos_Aires"


def _record_deps(
    *, visits: FakeRouteVisitRepository | None = None, enabled: set[str] | None = None
) -> RecordRouteVisitDependencies:
    return RecordRouteVisitDependencies(
        visits=visits or FakeRouteVisitRepository(),
        catalog=FakeModuleCatalogRepository(enabled),
        timezone=_TZ,
    )


async def test_records_a_visit_for_an_enabled_module() -> None:
    visits = FakeRouteVisitRepository()
    user_id = uuid.uuid4()
    await RecordRouteVisit(_record_deps(visits=visits, enabled={"sla"})).execute(
        user_id=user_id, raw_route="/sla/pendientes-a-cerrar"
    )
    assert any(u == user_id for (u, _d, _r) in visits.rows)


async def test_purges_old_rows_on_every_record() -> None:
    visits = FakeRouteVisitRepository()
    user_id = uuid.uuid4()
    await RecordRouteVisit(_record_deps(visits=visits, enabled={"sla"})).execute(
        user_id=user_id, raw_route="/sla/pendientes-a-cerrar"
    )
    assert len(visits.purged) == 1
    assert visits.purged[0][0] == user_id


async def test_rejects_a_malformed_route_before_touching_the_repo() -> None:
    visits = FakeRouteVisitRepository()
    with pytest.raises(InvalidRoutePathError):
        await RecordRouteVisit(_record_deps(visits=visits)).execute(
            user_id=uuid.uuid4(), raw_route="/liquidaciones/42"
        )
    assert visits.rows == {}


async def test_rejects_a_route_whose_module_is_not_enabled() -> None:
    with pytest.raises(UnknownRouteError):
        await RecordRouteVisit(_record_deps(enabled=set())).execute(
            user_id=uuid.uuid4(), raw_route="/sla/pendientes-a-cerrar"
        )


async def test_top_routes_ranks_by_visit_count_within_the_30_day_window() -> None:
    today = datetime.now(ZoneInfo(_TZ)).date()
    user_id = uuid.uuid4()
    other_user = uuid.uuid4()
    visits = FakeRouteVisitRepository(
        rows={
            (user_id, today - timedelta(days=1), "/insumos"): 5,
            (user_id, today - timedelta(days=2), "/sla/pendientes-a-cerrar"): 2,
            (user_id, today - timedelta(days=40), "/liquidaciones/lista"): 99,  # fuera de ventana
            (other_user, today - timedelta(days=1), "/insumos"): 50,  # de otro usuario
        }
    )
    deps = ListTopRoutesDependencies(visits=visits, timezone=_TZ)

    result = await ListTopRoutes(deps).execute(user_id=user_id, limit=6)

    assert [r.route for r in result] == ["/insumos", "/sla/pendientes-a-cerrar"]
    assert result[0].visits == 5
