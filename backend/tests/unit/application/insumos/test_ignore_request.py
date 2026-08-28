"""Tests de IgnoreRequest — ignorado PERMANENTE de una solicitud en HP SDS.

A diferencia de DismissRequest (IGNORE temporal, con auto-UNIGNORE cuando el pedido
asociado resuelve), acá el descarte no se revierte solo — ver ignore_request.py.
"""

from src.modules.insumos.application.dtos.request_actions import IgnoreCommand
from src.modules.insumos.application.use_cases.ignore_request import (
    IgnoreRequest,
    IgnoreRequestPorts,
)
from src.modules.insumos.domain.entities.audit_record import EVENT_IGNORED
from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CANCELLED,
    ProcessedRequest,
)
from tests.unit.domain.insumos.fakes import (
    FakeDismissedSupplyRepository,
    FakeInsightGateway,
    FakeOrderAuditRepository,
    FakeProcessedRequestRepository,
)


class World:
    def __init__(self) -> None:
        self.insight = FakeInsightGateway()
        self.processed = FakeProcessedRequestRepository()
        self.audit = FakeOrderAuditRepository()
        self.dismissed = FakeDismissedSupplyRepository()
        self.use_case = IgnoreRequest(
            IgnoreRequestPorts(
                insight=self.insight,  # type: ignore[arg-type]
                processed=self.processed,
                audit=self.audit,
                dismissed=self.dismissed,
            )
        )


async def test_con_pedido_asociado_ignora_y_suprime_sin_revertirse_solo() -> None:
    world = World()
    command = IgnoreCommand(
        hp_request_id=974325,
        customer_id=8,
        customer_name="Cliente Test",
        device_serial="SERIE1",
        sku="CF230A",
        supply_id="442759-7",
        supply_status="Despachado",
    )

    result = await world.use_case.execute(command)

    assert result.ok is True
    call = world.insight.updates[0]
    assert call["statusUpdate"] == "IGNORE"
    assert "442759-7" in call["comment"]
    record = world.audit.records[0]
    assert record.event == EVENT_IGNORED
    entry = world.dismissed.entries[442759]
    # hp_request_id=None: nunca entra a get_pending_unignore, no se revierte solo.
    assert entry.hp_request_id is None


async def test_sin_pedido_asociado_ignora_sin_tocar_dismissed_supplies() -> None:
    world = World()
    command = IgnoreCommand(
        hp_request_id=974325,
        customer_id=8,
        device_serial="SERIE1",
        sku="CF230A",
    )

    result = await world.use_case.execute(command)

    assert result.ok is True
    assert world.insight.updates[0]["statusUpdate"] == "IGNORE"
    assert world.dismissed.entries == {}


async def test_supply_id_con_formato_invalido_no_llama_a_hp_sds() -> None:
    world = World()
    command = IgnoreCommand(
        hp_request_id=974325, customer_id=8, device_serial="SERIE1", sku="CF230A",
        supply_id="no-es-un-id",
    )

    result = await world.use_case.execute(command)

    assert result.ok is False
    assert result.error is not None and "número de pedido" in result.error
    assert world.insight.updates == []


async def test_libera_el_registro_local_si_existia() -> None:
    world = World()
    await world.processed.mark_processed(
        ProcessedRequest(
            hp_request_id=974325, device_serial="SERIE1", sku="CF230A",
            internal_order_id="441770-2",
        )
    )
    command = IgnoreCommand(hp_request_id=974325, customer_id=8, device_serial="SERIE1")

    await world.use_case.execute(command)

    assert world.processed.rows[974325].status == STATUS_CANCELLED


async def test_si_insight_falla_no_registra_nada() -> None:
    world = World()
    world.insight.update_error = RuntimeError("Insight caído")
    command = IgnoreCommand(hp_request_id=974325, customer_id=8, device_serial="SERIE1")

    result = await world.use_case.execute(command)

    assert result.ok is False
    assert world.audit.records == []
