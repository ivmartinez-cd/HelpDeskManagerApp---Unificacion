"""Evento del historial permanente (order_audit) — nunca se borra; es la fuente de
todas las estadísticas y del techo anti-abuso count_created_today (que cuenta acá y
no en processed_requests porque cancelar borra el rastro allá, no acá)."""

from dataclasses import dataclass
from datetime import datetime

EVENT_CREATED = "CREATED"
EVENT_FAILED = "FAILED"
EVENT_RELEASED = "RELEASED"
EVENT_CANCELLED = "CANCELLED"
EVENT_DISMISSED = "DISMISSED"
# Descarte automático de la ventana de validación 0% (falsa alarma de sensor) — a
# diferencia de DISMISSED (descarte manual del operador).
EVENT_AUTO_DISMISSED = "AUTO_DISMISSED"
EVENT_DEVICE_DELETED = "DEVICE_DELETED"

ORDER_TYPE_SUPPLY = "supply"
ORDER_TYPE_INCIDENT = "incident"


@dataclass(frozen=True)
class AuditRecord:
    event: str
    hp_request_id: int | None = None
    customer_id: int | None = None
    customer_name: str | None = None
    device_serial: str | None = None
    sku: str | None = None
    internal_order_id: str | None = None
    detail: str | None = None
    dry_run: bool = False
    hp_request_time: datetime | None = None
    description: str | None = None
    device_id: int | None = None
    order_type: str = ORDER_TYPE_SUPPLY
    initial_percent_left: int | None = None
    initial_days_left: int | None = None
    initial_pages_left: int | None = None


@dataclass(frozen=True)
class StoredAuditRecord(AuditRecord):
    """Un evento ya persistido, tal como lo lee el Historial (con id y timestamp)."""

    audit_id: int = 0
    created_at: datetime | None = None


@dataclass(frozen=True)
class AuditSnapshot:
    """Backfill de device_id/initial_* para una fila grabada sin esa captura (filas
    anteriores a que order_audit la guardara) — se persiste al resolverla en vivo
    contra Insight para no repetir ese lookup en cada GET siguiente."""

    audit_id: int
    device_id: int
    initial_percent_left: int | None = None
    initial_days_left: int | None = None
    initial_pages_left: int | None = None
