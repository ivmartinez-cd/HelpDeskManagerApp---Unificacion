"""Tests de ListAudit — el Historial (GET /api/insumos/audit)."""

from src.modules.insumos.application.dtos.audit_query import ListAuditQuery
from src.modules.insumos.application.use_cases.list_audit import ListAudit, ListAuditPorts
from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CANCELLED,
    EVENT_CREATED,
    EVENT_DISMISSED,
    ORDER_TYPE_INCIDENT,
    AuditRecord,
)
from src.modules.insumos.domain.value_objects.audit_history import ACTION_CANCEL, SCOPE_SYSTEM
from tests.unit.domain.insumos.fakes import (
    FakeInsightGateway,
    FakeOrderAuditRepository,
    settings,
)


class World:
    def __init__(self) -> None:
        self.audit = FakeOrderAuditRepository()
        self.insight = FakeInsightGateway()
        self.use_case = ListAudit(
            ListAuditPorts(audit=self.audit, insight=self.insight),  # type: ignore[arg-type]
            settings(),
        )


def _query(**overrides: object) -> ListAuditQuery:
    base: dict[str, object] = {"page": 1, "size": 100}
    base.update(overrides)
    return ListAuditQuery(**base)  # type: ignore[arg-type]


def _created(order_id: str, **overrides: object) -> AuditRecord:
    base: dict[str, object] = {
        "event": EVENT_CREATED,
        "hp_request_id": 974325,
        "customer_id": 8,
        "customer_name": "Cliente Test",
        "device_serial": "SERIE1",
        "sku": "CF230A",
        "internal_order_id": order_id,
        "device_id": 7,
        "initial_percent_left": 5,
    }
    base.update(overrides)
    return AuditRecord(**base)  # type: ignore[arg-type]


async def test_lista_mas_reciente_primero_con_urls_del_portal() -> None:
    world = World()
    await world.audit.record(_created("441770-3"))
    await world.audit.record(_created("DRYRUN-SDS-974326", hp_request_id=974326, dry_run=True))
    await world.audit.record(
        _created("500123-4", hp_request_id=974327, order_type=ORDER_TYPE_INCIDENT)
    )

    rows, total = await world.use_case.execute(_query())

    assert total == 3
    assert [r.audit_id for r in rows] == [3, 2, 1]  # más reciente primero
    incident, dryrun, supply = rows
    assert incident.supply_url is not None and "/incidents/view/500123-4" in incident.supply_url
    assert dryrun.supply_url is None
    assert supply.supply_url is not None and supply.supply_url.endswith("/supplies/view/441770-3")


async def test_paginado_en_sql_no_en_memoria() -> None:
    world = World()
    for i in range(5):
        await world.audit.record(_created(f"44100{i}-1", hp_request_id=974000 + i))

    rows, total = await world.use_case.execute(_query(page=2, size=2))

    assert total == 5
    assert [r.audit_id for r in rows] == [3, 2]


async def test_fila_sin_device_id_se_enriquece_desde_insight_y_se_persiste() -> None:
    """Filas grabadas antes de que order_audit capturara device_id/initial_* (van a
    entrar también con la importación del legacy): se completan con la solicitud que
    Insight todavía trackea y el backfill evita repetir el lookup en cada GET."""
    world = World()
    await world.audit.record(
        _created("441770-3", device_id=None, initial_percent_left=None)
    )
    world.insight.actioned_by_customer[8] = [
        {"id": 974325, "deviceId": 7, "requestedLevel": 12, "requestedDaysLeft": 3}
    ]

    rows, _ = await world.use_case.execute(_query())

    row = rows[0]
    assert row.device_id == 7
    assert row.initial_percent_left == 12  # requestedLevel, no el nivel de hoy
    assert row.initial_days_left == 3
    assert len(world.audit.backfills) == 1
    assert world.audit.backfills[0].device_id == 7
    # El próximo GET ya no necesita Insight: la fila quedó completa.
    assert world.audit.stored[0].device_id == 7


async def test_si_insight_ya_no_trackea_la_solicitud_no_se_inventa_nada() -> None:
    world = World()
    await world.audit.record(
        AuditRecord(
            event=EVENT_DISMISSED,
            hp_request_id=974999,
            customer_id=8,
            device_serial="SERIE1",
            sku="CF230A",
        )
    )

    rows, _ = await world.use_case.execute(_query())

    assert rows[0].device_id is None
    assert rows[0].initial_percent_left is None
    assert world.audit.backfills == []


async def test_error_de_insight_no_rompe_el_historial() -> None:
    world = World()
    await world.audit.record(_created("441770-3", device_id=None))
    world.insight.errors_by_customer[8] = ConnectionError("timeout")

    rows, total = await world.use_case.execute(_query())

    assert total == 1
    assert rows[0].device_id is None  # queda como está, se reintenta en el próximo GET


async def test_fila_completa_no_dispara_lookups_a_insight() -> None:
    world = World()
    await world.audit.record(_created("441770-3"))  # ya tiene device_id
    world.insight.errors_by_customer[8] = ConnectionError("no debería llamarse")

    rows, _ = await world.use_case.execute(_query())

    assert rows[0].device_id == 7
    assert world.audit.backfills == []


async def test_los_filtros_llegan_al_repo() -> None:
    """scope=system solo trae eventos de sistema — filtrado real contra el
    repo, no en memoria acá."""
    world = World()
    await world.audit.record(_created("441770-3"))  # CREATED, de pedidos
    await world.audit.record(
        AuditRecord(event=EVENT_CANCELLED, hp_request_id=974325, customer_id=8)
    )

    rows, total = await world.use_case.execute(_query(scope=SCOPE_SYSTEM))

    assert total == 0
    assert rows == []


async def test_action_sale_poblado_usando_closures_for() -> None:
    world = World()
    await world.audit.record(_created("441770-3"))  # único CREATED real, sin cierre

    rows, _ = await world.use_case.execute(_query())

    assert rows[0].action == ACTION_CANCEL


async def test_closures_for_se_llama_solo_con_hp_request_id_no_nulos() -> None:
    world = World()
    await world.audit.record(_created("441770-3", hp_request_id=974325))
    await world.audit.record(
        AuditRecord(event=EVENT_DISMISSED, hp_request_id=None, customer_id=8)
    )

    await world.use_case.execute(_query())

    assert len(world.audit.closures_for_calls) == 1
    assert sorted(world.audit.closures_for_calls[0]) == [974325]
