"""Tests de ListRequests — el port de GET /api/requests contra fakes (servicios de
dominio reales para matching y lookup del portal)."""

from datetime import UTC, datetime

from src.modules.insumos.application.use_cases.get_dashboard import GetDashboardPorts
from src.modules.insumos.application.use_cases.list_requests import (
    ListRequests,
    ListRequestsConfig,
    ListRequestsPorts,
)
from src.modules.insumos.application.use_cases.validation_window import (
    ValidationWindow,
    ValidationWindowPorts,
)
from src.modules.insumos.domain.entities.audit_record import EVENT_RELEASED
from src.modules.insumos.domain.entities.customer_config import CustomerConfig
from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CANCELLED,
    ProcessedRequest,
)
from src.modules.insumos.domain.repositories.insight_gateway import JsonDict
from src.modules.insumos.domain.services.supply_lookup import CanalDirectoSupplyLookup
from src.modules.insumos.domain.services.validation_diagnosis import ValidationDiagnosis
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdSupply
from src.modules.insumos.domain.value_objects.pending_validation import PendingValidation
from tests.unit.domain.insumos.fakes import (
    FakeCustomerConfigRepository,
    FakeInsightGateway,
    FakeInsumosSettingsRepository,
    FakeOrderAuditRepository,
    FakeProcessedRequestRepository,
    FakeRequestValidationRepository,
    FakeSupplyCacheRepository,
    FakeWsAycGateway,
    settings,
)


def _insight_request(
    request_id: int,
    days_left: int = 5,
    sku: str = "CF230A",
    description: str = "Cartucho negro HP 30A",
    percent_left: float = 5.0,
) -> JsonDict:
    return {
        "id": request_id,
        "deviceId": 7,
        "requested": "2026-08-10T10:00:00.000Z",
        "consumable": {
            "sku": sku,
            "description": description,
            "daysLeft": days_left,
            "percentLeft": percent_left,
            "pagesLeft": 120,
            "index": 0,
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
        self.settings_repo = FakeInsumosSettingsRepository()
        self.audit = FakeOrderAuditRepository()
        self.validations = FakeRequestValidationRepository()

        self.customers.customers = [CustomerConfig(customer_id=8, name="Cliente Test")]
        self.insight.requests_by_customer = {8: []}
        self.insight.devices_by_id[7] = {
            "deviceId": 7,
            "serialNumber": "SERIE1",
            "extendedFields": {"zone": "HANGAR"},
            "lastContact": "2026-08-09T12:00:00.000Z",
        }
        self.wsayc.supplies_by_id = {}
        self.wsayc.supplies_for_empresa = []

        order_settings = settings()
        dashboard_ports = GetDashboardPorts(
            insight=self.insight,  # type: ignore[arg-type]
            wsayc=self.wsayc,
            processed=self.processed,
            supply_cache=self.supply_cache,
            customers=self.customers,
            settings=self.settings_repo,
            audit=self.audit,
        )
        self.window = ValidationWindow(
            ValidationWindowPorts(
                insight=self.insight,  # type: ignore[arg-type]
                validations=self.validations,
                audit=self.audit,
                diagnosis=ValidationDiagnosis(self.insight, self.wsayc),  # type: ignore[arg-type]
            )
        )
        ports = ListRequestsPorts(
            dashboard=dashboard_ports,
            validations=self.validations,
            supply_lookup=CanalDirectoSupplyLookup(self.wsayc, self.supply_cache, order_settings),
            validation_window=self.window,
        )
        config = ListRequestsConfig(
            order_settings=order_settings,
            insight_base_url="https://hp-sds-latam.insightportal.net/PortalAPI",
        )
        self.use_case = ListRequests(ports, config)


async def test_filas_enriquecidas_y_ordenadas_por_days_left() -> None:
    world = World()
    world.insight.requests_by_customer = {
        8: [_insight_request(1, days_left=10), _insight_request(2, days_left=2)]
    }

    rows = await world.use_case.execute(customer_id=8)

    assert [r.request_id for r in rows] == [2, 1]  # más urgente primero
    urgente = rows[0]
    assert urgente.serial == "SERIE1"
    assert urgente.store == "HANGAR"
    assert urgente.customer_name == "Cliente Test"
    assert urgente.status_key == "critical"
    assert urgente.status_label == "Crítico"
    assert rows[1].status_key == "warning"
    assert urgente.time == "10/08 07:00"  # 10:00Z en hora Argentina
    assert urgente.consumable_url.endswith("/PortalWeb/devices/7")


async def test_pedido_propio_activo_muestra_su_estado_en_vivo() -> None:
    world = World()
    world.insight.requests_by_customer = {8: [_insight_request(1)]}
    await world.processed.mark_processed(
        ProcessedRequest(hp_request_id=1, device_serial="SERIE1", sku="CF230A",
                         internal_order_id="441000-1")
    )
    world.wsayc.supplies_by_id = {
        441000: CdSupply(supply_id=441000, estado="Despachado", nro_serie_solicitud="SERIE1")
    }

    rows = await world.use_case.execute(customer_id=8)

    row = rows[0]
    assert row.order_id == "441000-1"
    assert row.supply_id == "441000-1"
    assert row.supply_status == "Despachado"
    assert row.supply_url is not None and row.supply_url.endswith("/supplies/view/441000-1")


async def test_pedido_propio_anulado_libera_y_vuelve_a_sin_cargar() -> None:
    world = World()
    world.insight.requests_by_customer = {8: [_insight_request(1)]}
    await world.processed.mark_processed(
        ProcessedRequest(hp_request_id=1, device_serial="SERIE1", sku="CF230A",
                         internal_order_id="441000-1")
    )
    world.wsayc.supplies_by_id = {
        441000: CdSupply(supply_id=441000, estado="Anulado", nro_serie_solicitud="SERIE1")
    }

    rows = await world.use_case.execute(customer_id=8)

    row = rows[0]
    assert row.order_id is None  # vuelve a la pestaña "Sin cargar"
    assert row.supply_id == "441000-1"
    assert row.supply_status == "Anulado"
    assert world.processed.rows[1].status == STATUS_CANCELLED
    released = [r for r in world.audit.records if r.event == EVENT_RELEASED]
    assert len(released) == 1


async def test_pedido_externo_activo_del_mismo_consumible_se_asocia_sin_order_id() -> None:
    world = World()
    world.insight.requests_by_customer = {8: [_insight_request(1)]}
    await world.supply_cache.upsert(
        [
            CachedSupply(
                supply_id=441500, serial="SERIE1", estado="Pendiente",
                description="Cartucho negro HP 30A",
            )
        ]
    )

    rows = await world.use_case.execute(customer_id=8)

    row = rows[0]
    assert row.order_id is None
    assert row.supply_id == "441500-6"
    assert row.supply_status == "Pendiente"


async def test_supply_posterior_a_la_solicitud_se_adopta_como_order_id() -> None:
    """Date-match del legacy: un supply (incluso ya Entregado) creado en o después de la
    fecha de la solicitud la cubre y se adopta como orderId."""
    world = World()
    world.insight.requests_by_customer = {8: [_insight_request(1)]}
    await world.supply_cache.upsert(
        [
            CachedSupply(
                supply_id=441600, serial="SERIE1", estado="Entregado",
                description="Cartucho negro HP 30A",
                fecha=datetime(2026, 8, 12, 10, 0, tzinfo=UTC),
            )
        ]
    )

    rows = await world.use_case.execute(customer_id=8)

    row = rows[0]
    assert row.supply_id == "441600-5"
    assert row.order_id == "441600-5"
    assert row.supply_status == "Entregado"


async def test_dry_run_muestra_estado_simulado() -> None:
    world = World()
    world.insight.requests_by_customer = {8: [_insight_request(1)]}
    await world.processed.mark_processed(
        ProcessedRequest(hp_request_id=1, device_serial="SERIE1", sku="CF230A",
                         internal_order_id="DRYRUN-SDS-1")
    )

    rows = await world.use_case.execute(customer_id=8)

    assert rows[0].supply_id == "DRYRUN-SDS-1"
    assert rows[0].supply_status == "Creado (Simulado)"
    assert rows[0].supply_url is None


async def test_validacion_pendiente_marca_la_fila() -> None:
    world = World()
    world.insight.requests_by_customer = {8: [_insight_request(1)]}
    world.validations.pending[1] = PendingValidation(
        hp_request_id=1,
        deadline_at=datetime(2026, 8, 10, 20, 0, tzinfo=UTC),
        swap_note="Cambio de insumo",
        diagnosis_headline="Posible falla de sensor",
    )

    rows = await world.use_case.execute(customer_id=8)

    row = rows[0]
    assert row.validation_pending is True
    assert row.validation_deadline == "2026-08-10T20:00:00Z"
    assert row.validation_swap_note == "Cambio de insumo"
    assert row.validation_diagnosis_headline == "Posible falla de sensor"


async def test_solicitud_elegible_en_cero_entra_en_validando() -> None:
    """Caso real MXBCQ7C03T: una solicitud elegible que llega en 0% exacto arranca su
    ventana de validación al verse en el dashboard — la fila sale marcada "Validando"
    con el diagnóstico ya calculado, sin esperar al poller."""
    world = World()
    world.insight.requests_by_customer = {
        8: [_insight_request(1, days_left=0, percent_left=0)]
    }

    rows = await world.use_case.execute(customer_id=8)

    assert len(world.validations.starts) == 1
    start = world.validations.starts[0]
    assert start.hp_request_id == 1
    assert start.device_serial == "SERIE1"
    assert start.initial_percent_left == 0
    assert start.deadline_minutes == 360  # validation_window_hours default (6hs)
    row = rows[0]
    assert row.validation_pending is True
    assert row.validation_diagnosis_headline == "Sin antecedentes claros — validar manualmente"


async def test_solicitud_elegible_no_cero_no_entra_en_validacion() -> None:
    """Nivel bajo pero no cero es una alerta legítima de HP SDS — no se valida."""
    world = World()
    world.insight.requests_by_customer = {8: [_insight_request(1, days_left=2)]}

    rows = await world.use_case.execute(customer_id=8)

    assert world.validations.starts == []
    assert rows[0].validation_pending is False


async def test_solicitud_en_cero_ya_cargada_no_entra_en_validacion() -> None:
    world = World()
    world.insight.requests_by_customer = {
        8: [_insight_request(1, days_left=0, percent_left=0)]
    }
    await world.processed.mark_processed(
        ProcessedRequest(hp_request_id=1, device_serial="SERIE1", sku="CF230A",
                         internal_order_id="441000-1")
    )

    await world.use_case.execute(customer_id=8)

    assert world.validations.starts == []


async def test_abrir_la_pantalla_resuelve_las_pendientes_contra_el_nivel_en_vivo() -> None:
    """resolve_pending corre ANTES de armar las filas: una validación cuya lectura en
    vivo ya se recuperó se descarta en el momento (AUTO_DISMISSED + DELETE en HP SDS)
    y la fila deja de mostrarse como "Validando"."""
    world = World()
    world.insight.requests_by_customer = {
        8: [_insight_request(1, days_left=0, percent_left=0)]
    }
    world.insight.consumables_by_device[7] = [{"sku": "CF230A", "percentLeft": 87, "index": 0}]
    # Ventana ya abierta por una vista anterior (larga: ni cerca de vencer).
    await world.window.start_pending(
        _insight_request(1, days_left=0, percent_left=0),
        device_id=7,
        customer_id=8,
        device_serial="SERIE1",
        deadline_minutes=360,
    )
    assert 1 in world.validations.pending

    rows = await world.use_case.execute(customer_id=8)

    assert world.validations.resolved == [(1, "DISMISSED")]
    assert rows[0].validation_pending is False
    dismissed = [r for r in world.audit.records if r.event == "AUTO_DISMISSED"]
    assert len(dismissed) == 1


async def test_error_de_un_cliente_no_rompe_el_listado_global() -> None:
    world = World()
    world.customers.customers = [
        CustomerConfig(customer_id=8, name="Sano"),
        CustomerConfig(customer_id=9, name="Roto"),
    ]
    world.insight.requests_by_customer = {8: [_insight_request(1)]}
    world.insight.errors_by_customer[9] = ConnectionError("timeout")

    rows = await world.use_case.execute(customer_id=None)

    assert [r.request_id for r in rows] == [1]
    assert rows[0].customer_name == "Sano"
