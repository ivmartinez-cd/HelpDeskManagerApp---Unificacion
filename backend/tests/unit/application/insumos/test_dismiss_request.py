"""Tests de DismissRequest — descarte manual de una solicitud en HP SDS.

DELETE cuando la solicitud no tiene un pedido activo asociado; IGNORE (temporal, con
auto-UNIGNORE vía dismiss_reconciliation.py) cuando sí lo tiene — ver dismiss_request.py.
"""

from src.modules.insumos.application.dtos.request_actions import DismissCommand
from src.modules.insumos.application.use_cases.dismiss_request import (
    DismissRequest,
    DismissRequestPorts,
)
from src.modules.insumos.domain.entities.audit_record import EVENT_DISMISSED
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

COMMAND = DismissCommand(
    hp_request_id=974325,
    customer_id=8,
    customer_name="Cliente Test",
    device_serial="SERIE1",
    sku="CF230A",
)

COMMAND_CON_PEDIDO_ACTIVO = DismissCommand(
    hp_request_id=974325,
    customer_id=8,
    customer_name="Cliente Test",
    device_serial="SERIE1",
    sku="CF230A",
    supply_id="442759-7",
    supply_status="Despachado",
)


class World:
    def __init__(self) -> None:
        self.insight = FakeInsightGateway()
        self.processed = FakeProcessedRequestRepository()
        self.audit = FakeOrderAuditRepository()
        self.dismissed = FakeDismissedSupplyRepository()
        self.use_case = DismissRequest(
            DismissRequestPorts(
                insight=self.insight,  # type: ignore[arg-type]
                processed=self.processed,
                audit=self.audit,
                dismissed=self.dismissed,
            )
        )


async def test_descarta_en_hp_sds_y_registra_en_el_historial() -> None:
    world = World()

    result = await world.use_case.execute(COMMAND)

    assert result.ok is True
    call = world.insight.updates[0]
    assert call["request_id"] == 974325
    assert call["statusUpdate"] == "DELETE"
    record = world.audit.records[0]
    assert record.event == EVENT_DISMISSED
    assert record.device_serial == "SERIE1"
    assert record.detail == "Solicitud descartada manualmente en HP SDS"


async def test_libera_el_registro_local_si_existia_un_pedido_vinculado() -> None:
    world = World()
    await world.processed.mark_processed(
        ProcessedRequest(hp_request_id=974325, device_serial="SERIE1", sku="CF230A",
                         internal_order_id="441770-2")
    )

    result = await world.use_case.execute(COMMAND)

    assert result.ok is True
    assert world.processed.rows[974325].status == STATUS_CANCELLED


async def test_si_insight_falla_no_se_registra_nada() -> None:
    """El detalle técnico va al log del server; el operador recibe un error genérico
    (a diferencia del legacy, que devolvía str(e) en un 500)."""
    world = World()
    world.insight.update_error = RuntimeError("Insight caído")

    result = await world.use_case.execute(COMMAND)

    assert result.ok is False
    assert result.error is not None and "No se pudo descartar" in result.error
    assert "Insight caído" not in result.error
    assert world.audit.records == []


async def test_con_pedido_activo_usa_ignore_y_registra_el_descarte() -> None:
    world = World()

    result = await world.use_case.execute(COMMAND_CON_PEDIDO_ACTIVO)

    assert result.ok is True
    call = world.insight.updates[0]
    assert call["statusUpdate"] == "IGNORE"
    assert "442759-7" in call["comment"]
    assert "Despachado" in call["comment"]
    entry = world.dismissed.entries[442759]
    assert entry.device_serial == "SERIE1"
    assert entry.hp_request_id == 974325  # se guarda para poder mandar UNIGNORE después


async def test_supply_id_dryrun_no_cuenta_como_pedido_activo() -> None:
    world = World()
    command = DismissCommand(
        hp_request_id=974325,
        customer_id=8,
        device_serial="SERIE1",
        sku="CF230A",
        supply_id="DRYRUN-SDS-974325",
    )

    result = await world.use_case.execute(command)

    assert result.ok is True
    assert world.insight.updates[0]["statusUpdate"] == "DELETE"
    assert world.dismissed.entries == {}
