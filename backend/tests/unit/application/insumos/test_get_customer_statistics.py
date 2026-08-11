"""Tests de GetCustomerStatistics — GET /api/insumos/estadisticas/clientes/{id}."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from src.modules.insumos.application.use_cases.get_customer_statistics import (
    GetCustomerStatistics,
    GetCustomerStatisticsPorts,
)
from src.modules.insumos.domain.entities.customer_config import CustomerConfig
from src.modules.insumos.domain.value_objects.audit_statistics import (
    DispatchRow,
    FulfillmentRow,
    SkuCount,
    SourceSplit,
)
from src.modules.insumos.domain.value_objects.cd_supply import SupplyStatusEvent
from src.shared.domain.errors import NotFoundError
from tests.unit.domain.insumos.fakes import (
    FakeAuditStatisticsRepository,
    FakeCustomerConfigRepository,
    FakeInsumosSettingsRepository,
    FakeKnownDeviceRepository,
    FakeSupplyCacheRepository,
)

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
HOY = datetime.now(TZ).date()
CLIENTE = 8


class World:
    def __init__(self) -> None:
        self.stats = FakeAuditStatisticsRepository()
        self.customers = FakeCustomerConfigRepository()
        self.devices = FakeKnownDeviceRepository()
        self.supply_cache = FakeSupplyCacheRepository()
        self.settings = FakeInsumosSettingsRepository()
        self.use_case = GetCustomerStatistics(
            GetCustomerStatisticsPorts(
                stats=self.stats,  # type: ignore[arg-type]
                customers=self.customers,  # type: ignore[arg-type]
                devices=self.devices,  # type: ignore[arg-type]
                supply_cache=self.supply_cache,  # type: ignore[arg-type]
                settings=self.settings,  # type: ignore[arg-type]
            ),
            TZ,
        )

    def with_customer(self, name: str = "Cliente Test") -> "World":
        self.customers.customers.append(
            CustomerConfig(customer_id=CLIENTE, name=name, enabled=True)
        )
        return self

    def with_totals(self, created: int, failed: int = 0, days: int = 7) -> "World":
        start = HOY - timedelta(days=days - 1)
        self.stats.totals_by_range[(start, HOY)] = {"CREATED": created, "FAILED": failed}
        return self


async def test_el_nombre_sale_del_padron_de_clientes() -> None:
    world = World().with_customer("Sucursal Centro")

    result = await world.use_case.execute(CLIENTE, days=7)

    assert result.customer_name == "Sucursal Centro"


async def test_cliente_podado_del_padron_conserva_el_nombre_del_historial() -> None:
    """Un cliente que ya no está en customers_config pero tiene pedidos viejos sigue
    siendo consultable — el nombre sale del último visto en order_audit."""
    world = World()
    world.stats.names[CLIENTE] = "Sucursal Vieja"

    result = await world.use_case.execute(CLIENTE, days=7)

    assert result.customer_name == "Sucursal Vieja"


async def test_cliente_sin_padron_ni_historial_no_existe() -> None:
    world = World()

    with pytest.raises(NotFoundError):
        await world.use_case.execute(999, days=7)


async def test_manual_es_el_resto_de_los_creados_no_una_consulta_aparte() -> None:
    world = World().with_customer()
    world.stats.split = SourceSplit(auto=7, total=10)

    result = await world.use_case.execute(CLIENTE, days=7)

    assert (result.auto_created, result.manual_created, result.auto_pct) == (7, 3, 70.0)


async def test_sin_pedidos_los_porcentajes_son_cero_y_no_dividen_por_cero() -> None:
    world = World().with_customer()

    result = await world.use_case.execute(CLIENTE, days=7)

    assert (result.success_rate, result.auto_pct) == (0.0, 0.0)
    assert result.fulfillment.coverage_pct == 0.0
    assert result.pending_to_dispatch.coverage_pct == 0.0


async def test_skus_distintos_cuenta_todos_pero_el_ranking_viaja_recortado() -> None:
    """Desviación consciente del legacy, que contaba el largo del ranking ya limitado
    a 10 y por eso nunca podía informar más de 10 SKUs distintos."""
    world = World().with_customer()
    world.stats.skus = [
        SkuCount(sku=f"SKU{i}", description=None, count=1) for i in range(14)
    ]

    result = await world.use_case.execute(CLIENTE, days=7)

    assert result.distinct_skus == 14
    assert len(result.top_skus) == 10


async def test_cobertura_del_tiempo_de_atencion_se_mide_sobre_el_total_creado() -> None:
    """`measured` < `totalCreated` es lo normal (pedidos sin hp_request_time): el
    porcentaje de cobertura es lo que evita leer el promedio como si aplicara a todos."""
    world = World().with_customer().with_totals(created=4)
    world.stats.fulfillment = [
        FulfillmentRow(
            sku="CF230A",
            device_serial="SERIE1",
            hp_request_time=datetime(2026, 6, 3, 12, tzinfo=UTC),  # 9hs ARG, miércoles
            created_at=datetime(2026, 6, 3, 13, tzinfo=UTC),
        )
    ]

    result = await world.use_case.execute(CLIENTE, days=7)

    assert result.fulfillment.measured == 1
    assert result.fulfillment.total_created == 4
    assert result.fulfillment.coverage_pct == 25.0
    assert result.fulfillment.avg_minutes == 60.0
    assert (result.fulfillment.work_hour_start, result.fulfillment.work_hour_end) == (8, 18)


async def test_el_horario_laboral_sale_de_la_configuracion_no_esta_fijo() -> None:
    world = World().with_customer()
    world.settings.raw = {"alert_work_hour_start": "9", "alert_work_hour_end": "17"}

    result = await world.use_case.execute(CLIENTE, days=7)

    assert (result.fulfillment.work_hour_start, result.fulfillment.work_hour_end) == (9, 17)


async def test_transito_a_despachado_usa_el_historial_de_estados_del_pedido() -> None:
    world = World().with_customer().with_totals(created=1)
    world.stats.dispatch = [
        DispatchRow(
            sku="CF230A",
            device_serial="SERIE1",
            internal_order_id="441770-3",
            created_at=datetime(2026, 6, 1, 12, tzinfo=UTC),
        )
    ]
    world.supply_cache.status_history[441770] = [
        SupplyStatusEvent(estado="Despachado", first_seen_at=datetime(2026, 6, 3, 12, tzinfo=UTC))
    ]

    result = await world.use_case.execute(CLIENTE, days=7)

    assert result.pending_to_dispatch.measured == 1
    assert result.pending_to_dispatch.avg_days == 2.0
    assert result.pending_to_dispatch.worst is not None
    assert result.pending_to_dispatch.worst.order_id == "441770-3"


async def test_equipos_monitoreados_son_los_del_cliente_pedido() -> None:
    world = World().with_customer()
    world.devices.monitored = {CLIENTE: 42, 99: 7}

    result = await world.use_case.execute(CLIENTE, days=7)

    assert result.monitored_devices == 42
