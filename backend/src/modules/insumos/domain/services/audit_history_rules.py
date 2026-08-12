"""Reglas puras del Historial: qué eventos trae cada pestaña y qué acción
ofrece cada fila — ver `domain/value_objects/audit_history.py` para el
vocabulario (AuditFilters, AuditClosures, scopes, eventos por scope)."""

from collections.abc import Sequence

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CREATED,
    EVENT_FAILED,
    ORDER_TYPE_SUPPLY,
    StoredAuditRecord,
)
from src.modules.insumos.domain.value_objects.audit_history import (
    ACTION_CANCEL,
    ACTION_RECONCILE,
    ORDER_EVENTS,
    SCOPE_ORDERS,
    SCOPE_SYSTEM,
    SYSTEM_EVENTS,
    AuditClosures,
)


def events_for_scope(scope: str, events: Sequence[str]) -> tuple[str, ...] | None:
    """Intersección del scope de pestaña con el filtro de evento (que puede ser
    múltiple: el <select> del frontend tiene una opción combinada "Anulado /
    liberado" = RELEASED+CANCELLED). Sin evento explícito, el scope solo. Sin
    scope (all) y sin evento, None (sin filtro)."""
    if scope == SCOPE_ORDERS:
        scope_events: tuple[str, ...] | None = ORDER_EVENTS
    elif scope == SCOPE_SYSTEM:
        scope_events = SYSTEM_EVENTS
    else:
        scope_events = None
    if not events:
        return scope_events
    if scope_events is None:
        return tuple(events)
    return tuple(e for e in scope_events if e in events)


def action_for(record: StoredAuditRecord, closures: AuditClosures) -> str | None:
    """Qué acción ofrece la fila, o None."""
    if (
        record.event == EVENT_CREATED
        and not record.dry_run
        and record.hp_request_id is not None
        and closures.last_closed.get(record.hp_request_id, 0) < record.audit_id
    ):
        return ACTION_CANCEL
    if (
        record.event == EVENT_FAILED
        and record.order_type == ORDER_TYPE_SUPPLY
        and record.customer_id is not None
        and record.hp_request_id is not None
        and record.hp_request_id not in closures.last_created
    ):
        return ACTION_RECONCILE
    return None
