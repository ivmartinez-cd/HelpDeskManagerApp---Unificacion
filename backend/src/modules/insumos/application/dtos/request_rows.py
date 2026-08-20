"""Fila de GET /api/insumos/requests — el shape que consume la tabla del dashboard.

Mutable a propósito: la fase de asociación (application/use_cases/_request_association)
va completando order/supply/validación sobre las filas ya armadas, igual que el legacy.
"""

from dataclasses import dataclass
from datetime import date


@dataclass
class RequestRow:
    request_id: int
    device_id: int
    customer_id: int | None
    customer_name: str | None
    store: str
    serial: str
    description: str
    sku: str
    percent_left: float | None
    days_left: int
    pages_left: int | None
    consumable_index: int | None
    consumable_url: str
    time: str  # dd/mm HH:MM local Argentina
    raw_time: str | None  # ISO crudo de Insight
    status_key: str
    status_label: str
    order_id: str | None
    requested_percent: float | None
    requested_days_left: int | None
    last_contact: str | None
    days_offline: int | None
    is_stale_offline: bool
    requested_day: date | None = None  # día argentino de `requested` (para el date-match)
    is_maintenance_kit: bool = False
    validation_pending: bool = False
    validation_deadline: str | None = None
    validation_swap_note: str | None = None
    validation_diagnosis_headline: str | None = None
    validation_diagnosis_detail: str | None = None
    supply_id: str | None = None
    supply_url: str | None = None
    supply_status: str | None = None
    # Aviso de entrega alternativa (zona con observación "CARGAR PARA SUCURSAL: ...").
    # No hay forma de fijar la sucursal de entrega por SOAP (ver zone_delivery_notice.py),
    # así que esto solo alimenta un aviso — el operador cambia la sucursal a mano en
    # Canal Directo después de cargar. requiere_cambio_sucursal=True con sucursal_entrega
    # None significa que el patrón matcheó pero no se pudo extraer un nombre legible; ahí
    # la UI muestra observacion_zona completa.
    requiere_cambio_sucursal: bool = False
    sucursal_entrega: str | None = None
    observacion_zona: str | None = None
