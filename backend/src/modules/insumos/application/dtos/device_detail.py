"""DTOs de los reads de detalle de equipo/consumible (modal de detalle del dashboard) —
port de los modelos de routers/requests/models.py que consumían esos endpoints."""

from dataclasses import dataclass

SOURCE_SOAP = "soap"
SOURCE_LOCAL = "local"


@dataclass
class DeviceSupplyRow:
    """Un pedido de insumos en Canal Directo para una serie, venga de la fuente que
    venga (getTopSupplies, cache local del scan, o processed_requests propio).
    Mutable: la descripción se enriquece después del merge (ver GetDeviceSupplies)."""

    supply_id: int
    supply_id_full: str
    serial: str
    estado: str
    fecha: str
    sku: str
    descripcion: str
    supply_url: str | None
    source: str  # SOURCE_SOAP | SOURCE_LOCAL


@dataclass(frozen=True)
class ConsumableHistoryPoint:
    """Una lectura de nivel del historial de Insight — alimenta el gráfico del modal."""

    date: str
    level: int | None


@dataclass(frozen=True)
class ConsumableRequestHistoryRow:
    """Una solicitud (de cualquier workflowStatus) de HP SDS para un consumible puntual."""

    request_id: int
    requested: str
    status: str
    status_label: str
    reason: str | None
    requested_level: int | None
    requested_days_left: int | None


@dataclass(frozen=True)
class ConsumableDetailResult:
    """Datos ampliados de un consumible puntual — equivalente a los paneles 'Detalles de
    los consumibles' + 'Detalles de rendimiento' del portal HP. A diferencia de
    RequestRow (la foto de Insight al momento de la solicitud), es lectura EN VIVO."""

    model: str | None = None
    type: str | None = None
    colour: str | None = None
    serial_number: str | None = None
    sku: str | None = None
    adjusted_yield: int | None = None
    reorder_sku: str | None = None
    reorder_yield: int | None = None
    capacity: int | None = None
    percent_left: int | None = None
    days_left: int | None = None
    pages_left: int | None = None
    last_read: str | None = None
    # Ciclos de trabajo actuales del equipo (no viene en /consumables — se toma del paso
    # más reciente de /consumables/history, ver GetConsumableDetail).
    engine_cycles: int | None = None
    first_read: str | None = None
    days_monitored: int | None = None
    engine_cycles_monitored: int | None = None
