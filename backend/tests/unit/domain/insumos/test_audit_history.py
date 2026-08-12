"""Tests de las reglas puras del Historial: scope de pestaña (events_for_scope)
y acción por fila (action_for) — ver domain/services/audit_history_rules.py."""

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_AUTO_DISMISSED,
    EVENT_CANCELLED,
    EVENT_CREATED,
    EVENT_DEVICE_DELETED,
    EVENT_DISMISSED,
    EVENT_FAILED,
    EVENT_RELEASED,
    KNOWN_EVENTS,
    ORDER_TYPE_INCIDENT,
    ORDER_TYPE_SUPPLY,
    StoredAuditRecord,
)
from src.modules.insumos.domain.services.audit_history_rules import action_for, events_for_scope
from src.modules.insumos.domain.value_objects.audit_history import (
    ACTION_CANCEL,
    ACTION_RECONCILE,
    ORDER_EVENTS,
    SCOPE_ALL,
    SCOPE_ORDERS,
    SCOPE_SYSTEM,
    SYSTEM_EVENTS,
    AuditClosures,
)


def _record(**overrides: object) -> StoredAuditRecord:
    base: dict[str, object] = {
        "audit_id": 10,
        "event": EVENT_CREATED,
        "created_at": None,
        "hp_request_id": 974325,
        "customer_id": 8,
        "dry_run": False,
        "order_type": ORDER_TYPE_SUPPLY,
    }
    base.update(overrides)
    return StoredAuditRecord(**base)  # type: ignore[arg-type]


# ---- events_for_scope --------------------------------------------------


def test_scope_all_sin_evento_es_sin_filtro() -> None:
    assert events_for_scope(SCOPE_ALL, ()) is None


def test_scope_orders_sin_evento_es_order_events() -> None:
    assert events_for_scope(SCOPE_ORDERS, ()) == ORDER_EVENTS


def test_scope_system_sin_evento_es_system_events() -> None:
    assert events_for_scope(SCOPE_SYSTEM, ()) == SYSTEM_EVENTS


def test_scope_all_con_evento_devuelve_el_evento_solo() -> None:
    assert events_for_scope(SCOPE_ALL, (EVENT_CREATED,)) == (EVENT_CREATED,)


def test_scope_orders_con_evento_que_pertenece_al_scope() -> None:
    assert events_for_scope(SCOPE_ORDERS, (EVENT_CREATED,)) == (EVENT_CREATED,)


def test_scope_system_con_evento_de_otro_scope_es_interseccion_vacia() -> None:
    """scope=system + event=CREATED: CREATED nunca es un evento de sistema —
    intersección imposible, tupla vacía (0 filas), no un error."""
    assert events_for_scope(SCOPE_SYSTEM, (EVENT_CREATED,)) == ()


def test_valor_combinado_released_cancelled_del_frontend() -> None:
    """"Anulado / liberado" del <select> manda ambos eventos juntos."""
    result = events_for_scope(SCOPE_ALL, (EVENT_RELEASED, EVENT_CANCELLED))
    assert set(result or ()) == {EVENT_RELEASED, EVENT_CANCELLED}


def test_scope_orders_con_evento_combinado_intersecta() -> None:
    """RELEASED es de sistema, CANCELLED es de pedidos: en scope=orders solo
    queda CANCELLED."""
    result = events_for_scope(SCOPE_ORDERS, (EVENT_RELEASED, EVENT_CANCELLED))
    assert result == (EVENT_CANCELLED,)


def test_guard_rail_todo_evento_conocido_esta_clasificado() -> None:
    """Tiene que reventar el día que alguien agregue un 8º evento sin
    clasificarlo en ORDER_EVENTS o SYSTEM_EVENTS."""
    assert set(ORDER_EVENTS) | set(SYSTEM_EVENTS) == set(KNOWN_EVENTS)
    assert set(ORDER_EVENTS) & set(SYSTEM_EVENTS) == set()


# ---- action_for ----------------------------------------------------------


def test_created_real_sin_cierre_ofrece_cancelar() -> None:
    record = _record(audit_id=10, event=EVENT_CREATED)
    closures = AuditClosures(last_created={}, last_closed={})

    assert action_for(record, closures) == ACTION_CANCEL


def test_created_dry_run_no_ofrece_nada() -> None:
    record = _record(audit_id=10, event=EVENT_CREATED, dry_run=True)
    closures = AuditClosures(last_created={}, last_closed={})

    assert action_for(record, closures) is None


def test_created_sin_hp_request_id_no_ofrece_nada() -> None:
    record = _record(audit_id=10, event=EVENT_CREATED, hp_request_id=None)
    closures = AuditClosures(last_created={}, last_closed={})

    assert action_for(record, closures) is None


def test_created_con_cierre_posterior_no_ofrece_cancelar() -> None:
    record = _record(audit_id=10, event=EVENT_CREATED, hp_request_id=974325)
    closures = AuditClosures(last_created={}, last_closed={974325: 15})

    assert action_for(record, closures) is None


def test_created_recargado_despues_de_anular_ofrece_cancelar() -> None:
    """El caso que el frontend hoy resuelve mal: CREATED (id 20) con un
    CANCELLED anterior (id 12) en la misma solicitud — comparar por id, no por
    presencia, para no bloquear el segundo pedido real."""
    record = _record(audit_id=20, event=EVENT_CREATED, hp_request_id=974325)
    closures = AuditClosures(last_created={}, last_closed={974325: 12})

    assert action_for(record, closures) == ACTION_CANCEL


def test_failed_de_supply_sin_created_ofrece_vincular() -> None:
    record = _record(
        audit_id=10, event=EVENT_FAILED, order_type=ORDER_TYPE_SUPPLY, customer_id=8
    )
    closures = AuditClosures(last_created={}, last_closed={})

    assert action_for(record, closures) == ACTION_RECONCILE


def test_failed_con_created_existente_no_ofrece_vincular() -> None:
    record = _record(
        audit_id=10, event=EVENT_FAILED, order_type=ORDER_TYPE_SUPPLY, customer_id=8
    )
    closures = AuditClosures(last_created={974325: 5}, last_closed={})

    assert action_for(record, closures) is None


def test_failed_de_incidente_no_ofrece_vincular() -> None:
    record = _record(
        audit_id=10, event=EVENT_FAILED, order_type=ORDER_TYPE_INCIDENT, customer_id=8
    )
    closures = AuditClosures(last_created={}, last_closed={})

    assert action_for(record, closures) is None


def test_failed_sin_customer_id_no_ofrece_vincular() -> None:
    record = _record(
        audit_id=10, event=EVENT_FAILED, order_type=ORDER_TYPE_SUPPLY, customer_id=None
    )
    closures = AuditClosures(last_created={}, last_closed={})

    assert action_for(record, closures) is None


def test_evento_sin_regla_no_ofrece_nada() -> None:
    for event in (EVENT_DISMISSED, EVENT_RELEASED, EVENT_AUTO_DISMISSED, EVENT_DEVICE_DELETED):
        record = _record(audit_id=10, event=event)
        closures = AuditClosures(last_created={}, last_closed={})

        assert action_for(record, closures) is None
