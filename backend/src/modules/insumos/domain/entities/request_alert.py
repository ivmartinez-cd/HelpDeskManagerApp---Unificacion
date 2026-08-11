"""Alerta de "solicitud pendiente sin cargar" (request_alerts).

Ciclo de vida: TRIGGERED (pendiente, sin vencer) → ESCALATED (superó el umbral) →
ACKNOWLEDGED (alguien la está gestionando a mano) | RESOLVED (se cargó el pedido o
dejó de estar pendiente). Una RESOLVED se reabre como TRIGGERED si la misma solicitud
vuelve a aparecer pendiente (p.ej. porque se anuló el pedido asociado).
"""

from dataclasses import dataclass
from datetime import datetime

STATE_TRIGGERED = "TRIGGERED"
STATE_ESCALATED = "ESCALATED"
STATE_ACKNOWLEDGED = "ACKNOWLEDGED"
STATE_RESOLVED = "RESOLVED"


@dataclass(frozen=True)
class AlertPendingEntry:
    """Solicitud pendiente para sync_pending — se upsertea en request_alerts."""

    hp_request_id: int
    customer_id: int
    customer_name: str
    device_serial: str
    sku: str
    description: str
    requested_at: datetime | None


@dataclass(frozen=True)
class RequestAlert:
    hp_request_id: int
    customer_id: int | None
    customer_name: str
    device_serial: str
    sku: str
    description: str
    requested_at: datetime | None
    first_seen_at: datetime
    escalated_at: datetime | None
