"""Tests de GetStatisticsOverview — GET /api/insumos/estadisticas."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from src.modules.insumos.application.use_cases.get_statistics_overview import (
    GetStatisticsOverview,
    GetStatisticsOverviewPorts,
)
from src.modules.insumos.domain.value_objects.audit_statistics import (
    CustomerActivity,
    DailyEventCount,
    SkuCount,
)
from tests.unit.domain.insumos.fakes import FakeAuditStatisticsRepository

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
HOY = datetime.now(TZ).date()


class World:
    def __init__(self) -> None:
        self.stats = FakeAuditStatisticsRepository()
        self.use_case = GetStatisticsOverview(
            GetStatisticsOverviewPorts(stats=self.stats),  # type: ignore[arg-type]
            TZ,
        )


async def test_compara_contra_el_periodo_previo_del_mismo_largo() -> None:
    world = World()
    period_start = HOY - timedelta(days=6)
    world.stats.totals_by_range[(period_start, HOY)] = {"CREATED": 10, "FAILED": 2}
    previous_end = period_start - timedelta(days=1)
    world.stats.totals_by_range[(previous_end - timedelta(days=6), previous_end)] = {
        "CREATED": 4
    }

    result = await world.use_case.execute(days=7)

    assert (result.total_created, result.total_failed) == (10, 2)
    assert result.previous_created == 4
    assert result.period.days == 7


async def test_activos_y_skus_distintos_salen_del_universo_completo_no_del_top() -> None:
    """El ranking que viaja son 10, pero "clientes activos"/"SKUs distintos" cuentan
    todo el rango — si contaran el top serían siempre <= 10."""
    world = World()
    world.stats.customers = [
        CustomerActivity(
            customer_id=i, customer_name=f"C{i}", created=100 - i, failed=0, total=100 - i
        )
        for i in range(15)
    ]
    world.stats.skus = [SkuCount(sku=f"SKU{i}", description=None, count=1) for i in range(12)]

    result = await world.use_case.execute(days=30)

    assert (result.active_customers, result.distinct_skus) == (15, 12)
    assert len(result.top_customers) == 10
    assert len(result.top_skus) == 10


async def test_promedio_diario_se_reparte_sobre_los_dias_del_rango() -> None:
    world = World()
    world.stats.totals_by_range[(HOY - timedelta(days=9), HOY)] = {"CREATED": 25}

    result = await world.use_case.execute(days=10)

    assert result.daily_average == 2.5


async def test_sin_actividad_no_hay_dia_pico() -> None:
    world = World()
    world.stats.counts = [DailyEventCount(day=HOY, event="FAILED", count=3)]

    result = await world.use_case.execute(days=3)

    assert (result.peak_day, result.peak_day_count) == (None, 0)
    assert len(result.series) == 3


async def test_expone_el_dia_mas_viejo_con_historial() -> None:
    world = World()
    world.stats.earliest = date(2026, 1, 15)

    result = await world.use_case.execute()

    assert result.earliest_day == date(2026, 1, 15)
    assert result.period.days == 30  # default sin parámetros
