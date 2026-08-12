"""Query del Historial (GET /api/insumos/audit y /audit/summary) — parseada por
`audit_query` (presentation) y resuelta a `AuditFilters` (domain) acá."""

from dataclasses import dataclass
from datetime import date

from src.modules.insumos.domain.entities.audit_record import KNOWN_EVENTS
from src.modules.insumos.domain.errors import FiltroDeHistorialInvalidoError
from src.modules.insumos.domain.services.audit_history_rules import events_for_scope
from src.modules.insumos.domain.value_objects.audit_history import SCOPE_ALL, AuditFilters


@dataclass(frozen=True, slots=True)
class ListAuditQuery:
    page: int = 1
    size: int = 100
    scope: str = SCOPE_ALL
    events: tuple[str, ...] = ()  # crudo del query param, se cruza con el scope después
    start_day: date | None = None
    end_day: date | None = None
    search: str | None = None


def to_filters(query: ListAuditQuery) -> AuditFilters:
    """Filtros del listado: el scope de la pestaña sí acota los eventos."""
    _validate(query)
    return AuditFilters(
        events=events_for_scope(query.scope, query.events),
        start_day=query.start_day,
        end_day=query.end_day,
        search=_normalized_search(query.search),
    )


def to_summary_filters(query: ListAuditQuery) -> AuditFilters:
    """Filtros del resumen de badges: el scope se ignora, todos los eventos
    entran en `by_event` (el frontend suma según la pestaña)."""
    _validate(query)
    return AuditFilters(
        events=events_for_scope(SCOPE_ALL, query.events),
        start_day=query.start_day,
        end_day=query.end_day,
        search=_normalized_search(query.search),
    )


def _validate(query: ListAuditQuery) -> None:
    if (
        query.start_day is not None
        and query.end_day is not None
        and query.start_day > query.end_day
    ):
        raise FiltroDeHistorialInvalidoError("start_day debe ser menor o igual a end_day")
    unknown = [e for e in query.events if e not in KNOWN_EVENTS]
    if unknown:
        raise FiltroDeHistorialInvalidoError(f"Evento desconocido: {', '.join(unknown)}")


def _normalized_search(search: str | None) -> str | None:
    return search.strip() or None if search is not None else None
