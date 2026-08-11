"""DTO de GET /api/insumos/orders/pending — port de PendingOrderRow (pending_orders.py)."""

from dataclasses import dataclass, field
from datetime import datetime

from src.modules.insumos.domain.value_objects.cd_supply import SupplyStatusEvent


@dataclass
class PendingOrderRow:
    """Un pedido cargado por esta app que sigue circulando (en tránsito) en Canal Directo.

    No depende de que la alerta siga activa en Insight (OUTSTANDING/ACTIONED) para
    existir — es una vista directa de processed_requests + el estado real en CD. Pero
    SÍ usa Insight, como mejor esfuerzo, para el seguimiento día a día: initial_* es la
    foto de consumo al momento de cargar el pedido (guardada en processed_requests);
    current_* es la lectura más fresca de Insight si todavía trackea la solicitud —
    None si Insight ya no sabe nada de ella (nunca se inventa)."""

    hp_request_id: int
    customer_id: int
    customer_name: str | None
    device_id: int
    serial: str
    store: str
    sku: str
    description: str
    order_id: str
    supply_url: str | None
    # Estado real del pedido en CD (Pendiente/Remito Generado/Despachado/Entregado con
    # include_delivered=True) — nunca hardcodeado, ver cd_state.py.
    supply_status: str
    created_at: datetime | None
    initial_percent_left: int | None = None
    initial_days_left: int | None = None
    initial_pages_left: int | None = None
    current_percent_left: int | None = None
    current_days_left: int | None = None
    current_pages_left: int | None = None
    # Clasificación de current_days_left (mismos umbrales/colores que el Dashboard) —
    # None si no hay lectura actual.
    status_key: str | None = None
    status_label: str | None = None
    # Ciclo de vida observado en CD (Pendiente → Remito Generado → Despachado →
    # Entregado). Puede venir incompleto para pedidos anteriores a supply_status_history
    # — el frontend distingue "paso no registrado" de "paso no alcanzado", nunca
    # inventa una fecha.
    status_history: list[SupplyStatusEvent] = field(default_factory=list)
