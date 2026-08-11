"""DTOs de las acciones sobre solicitudes (/cancel, /dismiss, /reconcile).

Mismo contrato "status 200 SIEMPRE" que /load: éxito y errores de negocio viajan en
el body ({ok: true, ...} | {ok: false, error}).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CancelResult:
    ok: bool
    supply_status: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class DismissCommand:
    """customer/serial/sku solo alimentan el evento del Historial (metadatos) — la
    baja en HP SDS usa únicamente el hp_request_id del path."""

    hp_request_id: int
    customer_id: int | None = None
    customer_name: str = ""
    device_serial: str = ""
    sku: str = ""


@dataclass(frozen=True)
class DismissResult:
    ok: bool
    error: str | None = None


@dataclass(frozen=True)
class ReconcileCommand:
    hp_request_id: int
    customer_id: int
    customer_name: str = ""


@dataclass(frozen=True)
class ReconcileResult:
    ok: bool
    order_id: str | None = None
    supply_url: str | None = None
    # True si la solicitud ya estaba vinculada antes de este llamado (idempotente —
    # un doble click no rompe nada, solo devuelve lo que ya había).
    already_linked: bool = False
    error: str | None = None
