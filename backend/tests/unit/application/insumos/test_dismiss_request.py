"""Tests de DismissRequest — descarte manual de una solicitud en HP SDS."""

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


class World:
    def __init__(self) -> None:
        self.insight = FakeInsightGateway()
        self.processed = FakeProcessedRequestRepository()
        self.audit = FakeOrderAuditRepository()
        self.use_case = DismissRequest(
            DismissRequestPorts(
                insight=self.insight,  # type: ignore[arg-type]
                processed=self.processed,
                audit=self.audit,
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
