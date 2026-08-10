"""DTOs del caso de uso LoadOrder (POST /api/requests/{id}/load).

El contrato del legacy es "status 200 SIEMPRE": éxito y errores de negocio viajan en el
body ({ok: true, orderId, ...} | {ok: false, error, conflictType?, ...}). LoadOrderResult
modela ese contrato; presentation solo lo serializa.
"""

from dataclasses import dataclass, field

CONFLICT_PENDING_VALIDATION = "pending_validation"
CONFLICT_TODAY_ORDER = "today_order"
CONFLICT_ACTIVE_SUPPLY = "active_supply"
CONFLICT_AMBIGUOUS_INSUMO = "AMBIGUOUS_INSUMO"  # casing del legacy, el frontend lo matchea


@dataclass(frozen=True)
class LoadOrderCommand:
    """deviceId/serial/sku NUNCA vienen del cliente — se derivan releyendo Insight
    (diseño de seguridad del legacy: sin esto se podrían crear pedidos reales sin una
    alerta SDS genuina detrás)."""

    hp_request_id: int
    customer_id: int
    customer_name: str
    dry_run: bool = False
    force_override: bool = False
    override_insumo_id: str | None = None
    revision: bool = True


@dataclass(frozen=True)
class LoadOrderResult:
    ok: bool
    order_id: str | None = None
    supply_url: str | None = None
    warn: str | None = None
    error: str | None = None
    conflict_type: str | None = None
    conflict_data: dict[str, object] = field(default_factory=dict)
    insumo_options: list[dict[str, str]] = field(default_factory=list)


def success(order_id: str, supply_url: str | None, warn: str | None = None) -> LoadOrderResult:
    return LoadOrderResult(ok=True, order_id=order_id, supply_url=supply_url, warn=warn)


def failure(error: str) -> LoadOrderResult:
    return LoadOrderResult(ok=False, error=error)


def conflict(
    conflict_type: str, error: str, data: dict[str, object] | None = None
) -> LoadOrderResult:
    return LoadOrderResult(
        ok=False, error=error, conflict_type=conflict_type, conflict_data=data or {}
    )


@dataclass(frozen=True)
class ResolvedRequest:
    """La solicitud re-derivada del lado del servidor contra Insight."""

    hp_request_id: int
    device_id: int
    device_serial: str
    store_name: str
    sku: str
    description: str
    percent_left: float | None
    days_left: int | None
    pages_left: int | None
    requested: str | None  # ISO-Z crudo de Insight (hp_request_time)
    is_maintenance_kit: bool
    warn: str | None
