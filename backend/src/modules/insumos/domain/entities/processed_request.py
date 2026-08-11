"""Registro de idempotencia: una solicitud de Insight ya procesada (tabla
processed_requests). Nunca se borra — "cancelar" es pasar a STATUS_CANCELLED,
lo que permite recargar a mano pero evita que la autocarga la repita."""

from dataclasses import dataclass
from datetime import datetime

STATUS_CREATED = "CREATED"
STATUS_CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class ProcessedRequest:
    hp_request_id: int
    status: str = STATUS_CREATED
    device_id: int | None = None
    device_serial: str = ""
    customer_id: int | None = None
    sku: str = ""
    internal_order_id: str = ""
    description: str = ""
    initial_percent_left: int | None = None
    initial_days_left: int | None = None
    initial_pages_left: int | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class ProcessedInitialSnapshot:
    """Reparación de la foto inicial de consumo en pedidos cargados antes de que
    processed_requests la guardara — se completa con requestedLevel/requestedDaysLeft
    de Insight y se persiste para no repetir el fallback en cada refresh."""

    hp_request_id: int
    initial_percent_left: int | None
    initial_days_left: int | None
    initial_pages_left: int | None
