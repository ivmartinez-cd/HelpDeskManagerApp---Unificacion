"""Tests de ReconcileOrder — vinculación manual de un pedido ya existente en CD.

Caso real que motivó el endpoint: un evento FAILED cuya verificación post-creación
falló por lag de lectura de Canal Directo, aunque persistNewSupply sí creó el pedido."""

from src.modules.insumos.application.dtos.request_actions import ReconcileCommand
from src.modules.insumos.application.use_cases.reconcile_order import (
    ReconcileOrder,
    ReconcileOrderConfig,
    ReconcileOrderPorts,
)
from src.modules.insumos.domain.entities.audit_record import EVENT_CREATED
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.repositories.insight_gateway import JsonDict
from src.modules.insumos.domain.services.claimed_order_creation import ClaimedOrderCreation
from src.modules.insumos.domain.services.supply_lookup import CanalDirectoSupplyLookup
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdSupply
from tests.unit.domain.insumos.fakes import (
    FakeInsightGateway,
    FakeOrderAuditRepository,
    FakeOrderClaimRepository,
    FakeProcessedRequestRepository,
    FakeSupplyCacheRepository,
    FakeWsAycGateway,
    settings,
)

COMMAND = ReconcileCommand(hp_request_id=974325, customer_id=8, customer_name="Cliente Test")


def _insight_request() -> JsonDict:
    return {
        "id": 974325,
        "deviceId": 7,
        "requested": "2026-08-10T10:00:00.000Z",
        "consumable": {
            "sku": "CF230A",
            "description": "Cartucho negro HP 30A",
            "percentLeft": 4.6,
            "daysLeft": 2,
            "pagesLeft": 120,
        },
    }


class World:
    def __init__(self) -> None:
        self.insight = FakeInsightGateway()
        self.wsayc = FakeWsAycGateway()
        self.processed = FakeProcessedRequestRepository()
        self.supply_cache = FakeSupplyCacheRepository()
        self.audit = FakeOrderAuditRepository()
        self.claims = FakeOrderClaimRepository()

        self.insight.requests_by_customer = {8: [_insight_request()]}
        self.insight.devices_by_id[7] = {"deviceId": 7, "serialNumber": "SERIE1"}
        order_settings = settings()
        ports = ReconcileOrderPorts(
            insight=self.insight,  # type: ignore[arg-type]
            processed=self.processed,
            audit=self.audit,
            supply_lookup=CanalDirectoSupplyLookup(self.wsayc, self.supply_cache, order_settings),
            claimed_creation=ClaimedOrderCreation(self.claims),
        )
        config = ReconcileOrderConfig(
            order_settings=order_settings,
            insight_mark_actioned=True,
            insight_status_on_order="ACTION",
        )
        self.use_case = ReconcileOrder(ports, config)

    async def with_cd_order(self) -> None:
        """Un pedido real en CD con la referencia SDS-974325, visible solo vía cache
        (origen Interno) — el caso exacto que reconcile viene a resolver."""
        await self.supply_cache.upsert(
            [CachedSupply(supply_id=441770, serial="SERIE1", estado="Pendiente")]
        )
        self.wsayc.supplies_by_id = {
            441770: CdSupply(
                supply_id=441770, reference="SDS-974325", estado="Pendiente",
                nro_serie_solicitud="SERIE1",
            )
        }


async def test_vincula_el_pedido_encontrado_por_referencia_exacta() -> None:
    world = World()
    await world.with_cd_order()

    result = await world.use_case.execute(COMMAND)

    assert result.ok is True
    assert result.order_id == "441770-3"
    assert result.supply_url is not None and result.supply_url.endswith("441770-3")
    assert result.already_linked is False
    row = world.processed.rows[974325]
    assert row.internal_order_id == "441770-3"
    assert row.device_serial == "SERIE1"
    assert row.initial_percent_left == 5  # 4.6 redondeado
    record = world.audit.records[0]
    assert record.event == EVENT_CREATED
    assert record.detail is not None and "Vinculado manualmente" in record.detail
    # Insight marcada como accionada con la referencia CD.
    update = world.insight.updates[0]
    assert update["externalRef"] == "CD-441770-3"
    assert update["statusUpdate"] == "ACTION"


async def test_ya_vinculada_responde_idempotente_sin_buscar() -> None:
    world = World()
    await world.processed.mark_processed(
        ProcessedRequest(hp_request_id=974325, device_serial="SERIE1", sku="CF230A",
                         internal_order_id="441000-1")
    )

    result = await world.use_case.execute(COMMAND)

    assert result.ok is True
    assert result.already_linked is True
    assert result.order_id == "441000-1"
    assert world.audit.records == []  # no se re-registra nada


async def test_sin_pedido_con_esa_referencia_no_vincula_nada() -> None:
    world = World()
    await world.supply_cache.upsert(
        [CachedSupply(supply_id=441770, serial="SERIE1", estado="Pendiente")]
    )
    world.wsayc.supplies_by_id = {
        441770: CdSupply(supply_id=441770, reference="SDS-999999", estado="Pendiente")
    }

    result = await world.use_case.execute(COMMAND)

    assert result.ok is False
    assert result.error is not None and "No se encontró ningún pedido" in result.error
    assert 974325 not in world.processed.rows


async def test_solicitud_ya_no_pendiente_en_insight() -> None:
    world = World()
    world.insight.requests_by_customer = {8: []}

    result = await world.use_case.execute(COMMAND)

    assert result.ok is False
    assert result.error is not None and "ya no está pendiente" in result.error


async def test_error_de_insight_no_vincula() -> None:
    world = World()
    world.insight.requests_error = ConnectionError("timeout")

    result = await world.use_case.execute(COMMAND)

    assert result.ok is False
    assert result.error is not None and "verificar la solicitud contra Insight" in result.error
