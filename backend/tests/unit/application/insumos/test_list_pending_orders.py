"""Tests de ListPendingOrders — seguimiento de pedidos propios en tránsito en CD."""

from datetime import UTC, datetime, timedelta

from src.modules.insumos.application.use_cases.list_pending_orders import (
    ListPendingOrders,
    ListPendingOrdersPorts,
)
from src.modules.insumos.domain.entities.customer_config import CustomerConfig
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.value_objects.cd_supply import (
    CachedSupply,
    CdSupply,
    SupplyStatusEvent,
)
from tests.unit.domain.insumos.fakes import (
    FakeCustomerConfigRepository,
    FakeInsightGateway,
    FakeInsumosSettingsRepository,
    FakeProcessedRequestRepository,
    FakeSupplyCacheRepository,
    FakeWsAycGateway,
    settings,
)


class World:
    def __init__(self) -> None:
        self.insight = FakeInsightGateway()
        self.wsayc = FakeWsAycGateway()
        self.processed = FakeProcessedRequestRepository()
        self.cache = FakeSupplyCacheRepository()
        self.customers = FakeCustomerConfigRepository()
        self.settings_repo = FakeInsumosSettingsRepository()
        self.wsayc.default_supply = None
        self.wsayc.supplies_by_id = {}
        self.customers.customers.append(CustomerConfig(customer_id=8, name="Cliente Test"))
        self.use_case = ListPendingOrders(
            ListPendingOrdersPorts(
                insight=self.insight,  # type: ignore[arg-type]
                wsayc=self.wsayc,  # type: ignore[arg-type]
                processed=self.processed,  # type: ignore[arg-type]
                supply_cache=self.cache,  # type: ignore[arg-type]
                customers=self.customers,  # type: ignore[arg-type]
                settings=self.settings_repo,  # type: ignore[arg-type]
            ),
            settings(),
        )

    async def add_order(
        self, hp_request_id: int, order_id: str, estado: str | None, **overrides: object
    ) -> None:
        base: dict[str, object] = {
            "hp_request_id": hp_request_id,
            "device_id": 7,
            "device_serial": "MXBCQ7C03T",
            "customer_id": 8,
            "sku": "W9008MC",
            "internal_order_id": order_id,
            "description": "Toner W9008MC",
            "initial_percent_left": 8,
            "initial_days_left": 2,
            "created_at": datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
        }
        base.update(overrides)
        await self.processed.mark_processed(ProcessedRequest(**base))  # type: ignore[arg-type]
        if estado is not None:
            try:
                sid = int(order_id.split("-")[0])
            except ValueError:
                return
            self.wsayc.supplies_by_id[sid] = CdSupply(  # type: ignore[index]
                supply_id=sid, estado=estado, fecha="01/08/2026 10:00:00", empresa_id="8"
            )


async def test_solo_pedidos_en_transito_mas_viejos_primero() -> None:
    world = World()
    await world.add_order(974001, "441001-1", "Pendiente")
    await world.add_order(
        974002,
        "441002-2",
        "Despachado",
        created_at=datetime(2026, 7, 20, 12, 0, tzinfo=UTC),
    )
    await world.add_order(974003, "441003-3", "Entregado")
    await world.add_order(974004, "441004-4", "Anulado")

    rows = await world.use_case.execute(customer_id=None, include_delivered=False)

    assert [r.hp_request_id for r in rows] == [974002, 974001]  # más viejo primero
    assert rows[0].supply_status == "Despachado"
    assert rows[0].customer_name == "Cliente Test"
    assert rows[0].supply_url is not None and "441002" in rows[0].supply_url


async def test_estado_desconocido_no_desaparece_de_la_vista() -> None:
    """Lista negra, nunca whitelist: un estado intermedio nuevo de CD sigue visible."""
    world = World()
    await world.add_order(974001, "441001-1", "En Preparación")

    rows = await world.use_case.execute(customer_id=None, include_delivered=False)

    assert [r.supply_status for r in rows] == ["En Preparación"]


async def test_include_delivered_suma_solo_entregados_recientes() -> None:
    world = World()
    await world.add_order(974001, "441001-1", "Entregado")
    await world.add_order(974002, "441002-2", "Entregado")
    world.cache.status_history[441001] = [
        SupplyStatusEvent(estado="Pendiente", first_seen_at=datetime(2026, 7, 1, tzinfo=UTC)),
        SupplyStatusEvent(
            estado="Entregado", first_seen_at=datetime.now(UTC) - timedelta(days=2)
        ),
    ]
    world.cache.status_history[441002] = [
        SupplyStatusEvent(
            estado="Entregado", first_seen_at=datetime.now(UTC) - timedelta(days=30)
        ),
    ]

    rows = await world.use_case.execute(customer_id=None, include_delivered=True)

    assert [r.hp_request_id for r in rows] == [974001]
    assert [e.estado for e in rows[0].status_history] == ["Pendiente", "Entregado"]


async def test_soap_caido_cae_al_cache_local_en_vez_de_excluir() -> None:
    """Más vale un dato levemente viejo que ninguno."""
    world = World()
    await world.add_order(974001, "441001-1", None)  # el SOAP no lo ve
    world.cache.entries.append(
        CachedSupply(supply_id=441001, serial="MXBCQ7C03T", estado="Pendiente")
    )

    rows = await world.use_case.execute(customer_id=None, include_delivered=False)

    assert [r.supply_status for r in rows] == ["Pendiente"]


async def test_telemetria_actual_de_insight_y_severidad() -> None:
    world = World()
    await world.add_order(974001, "441001-1", "Pendiente")
    world.insight.requests_by_status = {
        "OUTSTANDING": [
            {
                "id": 974001,
                "consumable": {"percentLeft": 4, "daysLeft": 1, "pagesLeft": 300},
            }
        ]
    }
    world.insight.devices_by_id[7] = {"extendedFields": {"zone": "Sucursal Centro"}}

    rows = await world.use_case.execute(customer_id=None, include_delivered=False)

    row = rows[0]
    assert row.current_percent_left == 4
    assert row.current_days_left == 1
    assert row.status_key == "critical"
    assert row.store == "Sucursal Centro"
    assert row.initial_percent_left == 8  # la foto guardada, no la lectura de hoy


async def test_sin_telemetria_actual_no_se_inventa_nada() -> None:
    """Insight ya no trackea la solicitud: current_* y severidad quedan None."""
    world = World()
    await world.add_order(974001, "441001-1", "Pendiente")

    rows = await world.use_case.execute(customer_id=None, include_delivered=False)

    row = rows[0]
    assert row.current_percent_left is None
    assert row.status_key is None


async def test_foto_inicial_faltante_se_completa_con_requested_y_persiste() -> None:
    """Pedidos previos a que processed_requests guardara initial_*: se completan con
    requestedLevel/requestedDaysLeft (el valor AL MOMENTO de la solicitud) y el
    backfill evita repetir el fallback en cada refresh."""
    world = World()
    await world.add_order(
        974001, "441001-1", "Pendiente", initial_percent_left=None, initial_days_left=None
    )
    world.insight.requests_by_status = {
        "OUTSTANDING": [
            {
                "id": 974001,
                "requestedLevel": 9,
                "requestedDaysLeft": 3,
                "consumable": {"percentLeft": 2, "daysLeft": 0},
            }
        ]
    }

    rows = await world.use_case.execute(customer_id=None, include_delivered=False)

    assert rows[0].initial_percent_left == 9  # requestedLevel, no percentLeft actual
    assert rows[0].initial_days_left == 3
    stored = world.processed.rows[974001]
    assert stored.initial_percent_left == 9


async def test_fallos_de_insight_no_tiran_la_respuesta() -> None:
    """Equipo o telemetría caídos: store vacío y current_* None, nunca un 500."""
    world = World()
    await world.add_order(974001, "441001-1", "Pendiente")
    world.insight.requests_error = ConnectionError("timeout")

    rows = await world.use_case.execute(customer_id=None, include_delivered=False)

    assert len(rows) == 1
    assert rows[0].store == ""
    assert rows[0].current_percent_left is None


async def test_dryrun_y_filtro_por_cliente() -> None:
    world = World()
    await world.add_order(974001, "DRYRUN-SDS-974001", "Pendiente")
    await world.add_order(974002, "441002-2", "Pendiente", customer_id=9)
    await world.add_order(974003, "441003-3", "Pendiente")

    rows = await world.use_case.execute(customer_id=8, include_delivered=False)

    assert [r.hp_request_id for r in rows] == [974003]
