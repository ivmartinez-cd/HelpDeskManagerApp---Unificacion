"""Tests de GetAuditSummary — badges de las 5 pestañas del Historial
(GET /api/insumos/audit/summary)."""

from datetime import date

import pytest

from src.modules.insumos.application.dtos.audit_query import ListAuditQuery
from src.modules.insumos.application.use_cases.get_audit_summary import (
    GetAuditSummary,
    GetAuditSummaryPorts,
)
from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CREATED,
    EVENT_DISMISSED,
    EVENT_RELEASED,
    AuditRecord,
)
from src.modules.insumos.domain.errors import FiltroDeHistorialInvalidoError
from src.modules.insumos.domain.value_objects.audit_history import SCOPE_ORDERS, SCOPE_SYSTEM
from tests.unit.domain.insumos.fakes import FakeOrderAuditRepository


class World:
    def __init__(self) -> None:
        self.audit = FakeOrderAuditRepository()
        self.use_case = GetAuditSummary(GetAuditSummaryPorts(audit=self.audit))


def _query(**overrides: object) -> ListAuditQuery:
    base: dict[str, object] = {"page": 1, "size": 100}
    base.update(overrides)
    return ListAuditQuery(**base)  # type: ignore[arg-type]


async def test_orders_system_y_total_se_derivan_de_by_event() -> None:
    world = World()
    await world.audit.record(AuditRecord(event=EVENT_CREATED, hp_request_id=1, customer_id=8))
    await world.audit.record(AuditRecord(event=EVENT_CREATED, hp_request_id=2, customer_id=8))
    await world.audit.record(AuditRecord(event=EVENT_DISMISSED, hp_request_id=3, customer_id=8))
    await world.audit.record(AuditRecord(event=EVENT_RELEASED, hp_request_id=4, customer_id=8))

    summary = await world.use_case.execute(_query())

    assert summary.by_event == {"CREATED": 2, "DISMISSED": 1, "RELEASED": 1}
    assert summary.orders == 3  # CREATED x2 + DISMISSED
    assert summary.system == 1  # RELEASED
    assert summary.total == 4


async def test_el_scope_de_la_query_no_afecta_el_resultado() -> None:
    """El resumen siempre cuenta todos los eventos — el scope es cosa del
    listado (pestaña activa), no del conteo de badges."""
    world = World()
    await world.audit.record(AuditRecord(event=EVENT_CREATED, hp_request_id=1, customer_id=8))
    await world.audit.record(AuditRecord(event=EVENT_RELEASED, hp_request_id=2, customer_id=8))

    all_scope = await world.use_case.execute(_query())
    orders_scope = await world.use_case.execute(_query(scope=SCOPE_ORDERS))
    system_scope = await world.use_case.execute(_query(scope=SCOPE_SYSTEM))

    assert all_scope.by_event == orders_scope.by_event == system_scope.by_event
    assert all_scope.total == orders_scope.total == system_scope.total == 2


async def test_rango_invertido_levanta_error() -> None:
    world = World()

    with pytest.raises(FiltroDeHistorialInvalidoError):
        await world.use_case.execute(
            _query(start_day=date(2026, 8, 12), end_day=date(2026, 8, 1))
        )


async def test_sin_eventos_registrados_todo_es_cero() -> None:
    world = World()

    summary = await world.use_case.execute(_query())

    assert summary == type(summary)(by_event={}, orders=0, system=0, total=0)
