"""Equipo del inventario de SDS (known_devices).

SDS descubre equipos en la red de cada cliente, pero hasta que alguien los registra en
el portal quedan con `monitor_status` distinto de 'Y' y NO generan avisos de insumos —
por eso "equipos sin registrar" es una pantalla propia y no un detalle del inventario.
"""

from dataclasses import dataclass
from datetime import datetime

# Un equipo monitoreado ('Y') o en alta ('J') ya no cuenta como "sin registrar".
MONITORED_STATUSES = ("Y", "J")


@dataclass(frozen=True)
class DeviceInventoryEntry:
    """Una fila del inventario tal como la devuelve Insight, ya normalizada."""

    device_id: int
    customer_id: int
    serial: str
    model: str
    zone: str
    ip_address: str
    monitor_status: str
    monitor_name: str
    discovery_date: datetime | None
    last_contact: datetime | None


@dataclass(frozen=True)
class KnownDevice:
    """Lo que la pantalla de equipos sin registrar necesita — incluye el nombre del
    cliente, que vive en customers_config y no en known_devices."""

    device_id: int
    customer_id: int
    customer_name: str
    serial: str
    model: str
    zone: str
    ip_address: str
    monitor_status: str
    discovery_date: datetime | None
    last_contact: datetime | None
    first_seen_at: datetime
    dismissed: bool
