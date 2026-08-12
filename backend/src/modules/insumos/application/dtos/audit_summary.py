"""DTO del resumen del Historial (GET /api/insumos/audit/summary) — los
conteos por evento y por pestaña que alimentan los badges."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditSummary:
    by_event: dict[str, int]
    orders: int  # suma de ORDER_EVENTS
    system: int  # suma de SYSTEM_EVENTS
    total: int
