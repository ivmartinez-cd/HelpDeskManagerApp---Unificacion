"""Tests de CancelOrder — anulación manual del pedido asociado a una solicitud."""

from src.modules.insumos.application.use_cases.cancel_order import CancelOrder, CancelOrderPorts
from src.modules.insumos.domain.entities.audit_record import EVENT_CANCELLED
from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CANCELLED,
    ProcessedRequest,
)
from src.modules.insumos.domain.value_objects.cd_supply import CdSupply
from tests.unit.domain.insumos.fakes import (
    FakeOrderAuditRepository,
    FakeProcessedRequestRepository,
    FakeSupplyCacheRepository,
    FakeWsAycGateway,
)


class World:
    def __init__(self) -> None:
        self.wsayc = FakeWsAycGateway()
        self.processed = FakeProcessedRequestRepository()
        self.supply_cache = FakeSupplyCacheRepository()
        self.audit = FakeOrderAuditRepository()
        self.use_case = CancelOrder(
            CancelOrderPorts(
                wsayc=self.wsayc,
                processed=self.processed,
                supply_cache=self.supply_cache,
                audit=self.audit,
            )
        )

    async def with_processed(self, order_id: str = "441770-3") -> None:
        await self.processed.mark_processed(
            ProcessedRequest(
                hp_request_id=974325,
                device_serial="SERIE1",
                sku="CF230A",
                customer_id=8,
                internal_order_id=order_id,
                description="Cartucho negro HP 30A",
            )
        )


async def test_sin_pedido_cargado_no_hay_nada_que_anular() -> None:
    world = World()

    result = await world.use_case.execute(974325)

    assert result.ok is False
    assert result.error == "No hay un pedido cargado para esta solicitud."
    assert world.wsayc.voided_supplies == []


async def test_anula_el_supply_y_libera_el_registro_local() -> None:
    world = World()
    await world.with_processed()
    world.wsayc.incidents_by_id = {}  # no es un incidente
    world.wsayc.supplies_by_id = {
        441770: CdSupply(supply_id=441770, estado="Anulado", nro_serie_solicitud="SERIE1")
    }

    result = await world.use_case.execute(974325)

    assert result.ok is True
    assert result.supply_status == "Anulado"
    assert world.wsayc.voided_supplies == [441770]
    assert world.processed.rows[974325].status == STATUS_CANCELLED
    record = world.audit.records[0]
    assert record.event == EVENT_CANCELLED
    assert record.internal_order_id == "441770-3"
    assert record.detail is not None and "supply 441770" in record.detail
    # El cache refleja el estado nuevo al instante (bloqueo 2 de /load).
    assert world.supply_cache.entries[0].estado == "Anulado"
    assert world.supply_cache.entries[0].serial == "SERIE1"


async def test_anula_un_incidente_de_st_sin_tocar_el_cache_de_supplies() -> None:
    world = World()
    await world.with_processed(order_id="500123-4")
    # fetch_incident_by_id se llama dos veces (detección + confirmación post-void);
    # la detección solo mira el id, la confirmación lee el estado Anulado.
    world.wsayc.incidents_by_id = {500123: CdSupply(supply_id=500123, estado="Anulado")}

    result = await world.use_case.execute(974325)

    assert result.ok is True
    assert world.wsayc.voided_incidents == [500123]
    assert world.wsayc.voided_supplies == []
    assert world.supply_cache.entries == []  # los incidentes no van al cache de supplies
    assert world.audit.records[0].detail is not None
    assert "incidente 500123" in world.audit.records[0].detail


async def test_si_cd_no_confirma_la_anulacion_no_se_libera_nada() -> None:
    """voidSupply responde "true" incondicionalmente — si la relectura no muestra
    Anulado/Cancelado, el registro local queda intacto y se avisa al operador."""
    world = World()
    await world.with_processed()
    world.wsayc.supplies_by_id = {
        441770: CdSupply(supply_id=441770, estado="Pendiente", nro_serie_solicitud="SERIE1")
    }

    result = await world.use_case.execute(974325)

    assert result.ok is False
    assert result.error is not None and "no confirmó la anulación" in result.error
    assert "Pendiente" in result.error
    assert world.processed.rows[974325].status == "CREATED"
    assert world.audit.records == []


async def test_void_fallido_devuelve_error_sin_liberar() -> None:
    world = World()
    await world.with_processed()
    world.wsayc.void_supply_result = False

    result = await world.use_case.execute(974325)

    assert result.ok is False
    assert result.error is not None and "No se pudo anular el pedido" in result.error
    assert world.processed.rows[974325].status == "CREATED"


async def test_pedido_dryrun_no_se_puede_anular_en_cd() -> None:
    """Un pedido simulado no existe en Canal Directo — mismo error que el legacy."""
    world = World()
    await world.with_processed(order_id="DRYRUN-SDS-974325")

    result = await world.use_case.execute(974325)

    assert result.ok is False
    assert result.error == "No se pudo interpretar el número de pedido o incidente."


async def test_pedido_ya_cancelado_cuenta_como_sin_pedido() -> None:
    world = World()
    await world.with_processed()
    await world.processed.mark_cancelled(974325)

    result = await world.use_case.execute(974325)

    assert result.ok is False
    assert result.error == "No hay un pedido cargado para esta solicitud."
