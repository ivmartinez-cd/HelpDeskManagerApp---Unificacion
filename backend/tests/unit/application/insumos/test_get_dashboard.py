"""Tests del caso de uso GetDashboard (las 4 fases contra fakes)."""

from src.modules.insumos.application.use_cases.get_dashboard import (
    GetDashboard,
    GetDashboardPorts,
)
from src.modules.insumos.domain.entities.audit_record import EVENT_RELEASED
from src.modules.insumos.domain.entities.customer_config import CustomerConfig
from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CANCELLED,
    ProcessedRequest,
)
from src.modules.insumos.domain.repositories.insight_gateway import JsonDict
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdSupply
from tests.unit.domain.insumos.fakes import (
    FakeCustomerConfigRepository,
    FakeDismissedSupplyRepository,
    FakeInsightGateway,
    FakeInsumosSettingsRepository,
    FakeOrderAuditRepository,
    FakeProcessedRequestRepository,
    FakeSupplyCacheRepository,
    FakeWsAycGateway,
)


def _insight_request(
    request_id: int,
    days_left: int = 2,
    device_id: int = 7,
    sku: str = "CF230A",
    description: str = "Cartucho negro HP 30A",
) -> JsonDict:
    return {
        "id": request_id,
        "deviceId": device_id,
        "requested": "2026-08-10T10:00:00.000Z",
        "consumable": {
            "sku": sku,
            "description": description,
            "daysLeft": days_left,
            "percentLeft": 5.0,
            "reorderPart": {"type": "TONER"},
        },
    }


class World:
    def __init__(self) -> None:
        self.insight = FakeInsightGateway()
        self.wsayc = FakeWsAycGateway()
        self.processed = FakeProcessedRequestRepository()
        self.supply_cache = FakeSupplyCacheRepository()
        self.customers = FakeCustomerConfigRepository()
        self.settings = FakeInsumosSettingsRepository()
        self.audit = FakeOrderAuditRepository()
        self.dismissed = FakeDismissedSupplyRepository()

        self.customers.customers = [CustomerConfig(customer_id=8, name="Cliente Test")]
        self.insight.requests_by_customer = {8: []}
        self.insight.devices_by_id[7] = {"deviceId": 7, "serialNumber": "SERIE1"}
        self.wsayc.supplies_by_id = {}

        self.use_case = GetDashboard(
            GetDashboardPorts(
                insight=self.insight,  # type: ignore[arg-type]
                wsayc=self.wsayc,
                processed=self.processed,
                supply_cache=self.supply_cache,
                customers=self.customers,
                settings=self.settings,
                audit=self.audit,
                dismissed=self.dismissed,
            )
        )


async def test_dashboard_cuenta_pendientes_y_cargadas() -> None:
    world = World()
    world.insight.requests_by_customer = {
        8: [
            # Otro consumible de la misma serie: el pedido activo del procesado no la cubre.
            _insight_request(1, days_left=2, sku="W9008MC", description="Toner Cyan HP"),
            _insight_request(2),
        ]
    }
    await world.processed.mark_processed(
        ProcessedRequest(hp_request_id=2, device_serial="SERIE1", sku="CF230A",
                         internal_order_id="441000-1")
    )
    # El estado cacheado del pedido procesado sigue activo — no libera.
    await world.supply_cache.upsert(
        [CachedSupply(supply_id=441000, serial="SERIE1", estado="Pendiente")]
    )
    world.supply_cache.recently_cached = {441000}  # dentro del TTL: no re-verificar

    result = await world.use_case.execute(refresh_minutes=60)

    assert result.totals == {
        "pending": 1, "critical": 1, "urgent": 0, "warning": 0, "good": 0, "loaded": 1,
    }
    assert result.loaded_today == 1
    assert result.customers_enabled == 1
    assert result.thresholds.critical == 3
    assert result.refresh_minutes == 60


async def test_error_de_un_cliente_no_tira_el_dashboard() -> None:
    world = World()
    world.customers.customers = [
        CustomerConfig(customer_id=8, name="Sano"),
        CustomerConfig(customer_id=9, name="Roto"),
    ]
    world.insight.requests_by_customer = {8: [_insight_request(1)]}
    world.insight.errors_by_customer[9] = ConnectionError("timeout")

    result = await world.use_case.execute(refresh_minutes=60)

    roto = next(e for e in result.per_customer if e.name == "Roto")
    assert roto.error == "No se pudo consultar este cliente"
    assert result.totals["pending"] == 1  # el cliente sano se computó igual


async def test_pedido_anulado_en_cd_libera_la_solicitud() -> None:
    """Fases 2+3: el estado vivo del SOAP muestra Anulado → mark_cancelled + audit
    RELEASED, y la solicitud vuelve a contar como pendiente."""
    world = World()
    world.insight.requests_by_customer = {8: [_insight_request(1, days_left=20)]}
    await world.processed.mark_processed(
        ProcessedRequest(hp_request_id=1, device_serial="SERIE1", sku="CF230A",
                         internal_order_id="441000-1")
    )
    # Sin estado cacheado → se consulta en vivo; CD responde Anulado.
    world.wsayc.supplies_by_id = {
        441000: CdSupply(supply_id=441000, estado="Anulado", nro_serie_solicitud="SERIE1")
    }

    result = await world.use_case.execute(refresh_minutes=60)

    assert world.processed.rows[1].status == STATUS_CANCELLED
    released = [r for r in world.audit.records if r.event == EVENT_RELEASED]
    assert len(released) == 1
    assert released[0].detail == "supply 441000 Anulado"
    assert result.totals["pending"] == 1
    assert result.totals["loaded"] == 0


async def test_refresh_en_vivo_actualiza_el_cache() -> None:
    world = World()
    world.insight.requests_by_customer = {8: [_insight_request(1)]}
    await world.processed.mark_processed(
        ProcessedRequest(hp_request_id=1, device_serial="SERIE1", sku="CF230A",
                         internal_order_id="441000-1")
    )
    world.wsayc.supplies_by_id = {
        441000: CdSupply(
            supply_id=441000, estado="Despachado", nro_serie_solicitud="SERIE1",
            fecha="10/08/2026 09:00:00", empresa_id="8",
        )
    }

    await world.use_case.execute(refresh_minutes=60)

    cached = [e for e in world.supply_cache.entries if e.supply_id == 441000]
    assert cached and cached[0].estado == "Despachado"
    assert cached[0].serial == "SERIE1"


async def test_sin_clientes_habilitados_devuelve_todo_en_cero() -> None:
    world = World()
    world.customers.customers = []

    result = await world.use_case.execute(refresh_minutes=60)

    assert result.customers_enabled == 0
    assert result.totals["pending"] == 0
    assert result.per_customer == []
