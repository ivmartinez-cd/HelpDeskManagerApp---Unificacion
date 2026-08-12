"""Vocabulario del Historial (GET /api/insumos/audit): scope de pestaña, filtros
ya resueltos y los cierres de solicitud usados para calcular la acción de fila."""

from dataclasses import dataclass
from datetime import date

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_AUTO_DISMISSED,
    EVENT_DEVICE_DELETED,
    EVENT_RELEASED,
    KNOWN_EVENTS,
)

SCOPE_ORDERS, SCOPE_SYSTEM, SCOPE_ALL = "orders", "system", "all"

# DESVÍO CONSCIENTE DEL LEGACY, espejo exacto de isSystemEvent en el frontend
# (frontend/src/features/insumos/components/historial/audit-events.ts): allá
# "sistema" era solo DEVICE_DELETED; acá RELEASED y AUTO_DISMISSED también son
# automáticos (no los dispara un click del operador).
SYSTEM_EVENTS: tuple[str, ...] = (EVENT_RELEASED, EVENT_AUTO_DISMISSED, EVENT_DEVICE_DELETED)
ORDER_EVENTS: tuple[str, ...] = tuple(e for e in KNOWN_EVENTS if e not in SYSTEM_EVENTS)

ACTION_CANCEL, ACTION_RECONCILE = "cancel", "reconcile"


@dataclass(frozen=True)
class AuditFilters:
    """Filtros ya resueltos: `events` combina el scope de pestaña con el filtro
    de evento del <select>, así el adaptador solo ve una lista. None = sin
    filtro; tupla vacía = intersección imposible (scope=system + event=CREATED)
    → 0 filas, no un error."""

    events: tuple[str, ...] | None = None
    start_day: date | None = None  # día calendario ARGENTINO sobre created_at
    end_day: date | None = None
    search: str | None = None


@dataclass(frozen=True)
class AuditClosures:
    """Para los hp_request_id de una página: el id (no bool) del último CREATED
    y del último cierre (CANCELLED/RELEASED). Se calcula sobre TODA la tabla,
    nunca sobre la página ni sobre el filtro — es justo lo que el frontend no
    puede saber con lo que tiene cargado."""

    last_created: dict[int, int]
    last_closed: dict[int, int]
