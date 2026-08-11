"""Value objects del flujo de equipos offline."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class CdVerdict(StrEnum):
    BODEGA = "BODEGA"
    OTRO_CLIENTE = "OTRO_CLIENTE"
    EN_CLIENTE = "EN_CLIENTE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class OfflineDevice:
    """Equipo offline tal como lo devuelve list_offline — snapshot local, sin red."""

    device_id: int
    customer_id: int
    customer_name: str
    serial: str
    model: str
    zone: str
    last_contact: datetime | None
    monitor_name: str
    cd_status: str
    cd_detail: str
    cd_checked_at: datetime | None
    offline_dismissed: bool


@dataclass(frozen=True)
class DeviceLocationUpdate:
    """Resultado de un getMachineBySerial — persiste en cd_status/cd_detail/cd_checked_at."""

    device_id: int
    cd_status: str
    cd_detail: str


@dataclass(frozen=True)
class MassOutage:
    """Caída de colector o salida masiva de equipos en un mismo día — excluidos de la baja."""

    customer_id: int
    customer_name: str
    # YYYY-MM-DD en UTC — mínimo de last_contact del grupo (outage confirmado) o día del evento
    day: str
    device_ids: tuple[int, ...]
    fleet_size: int = 0
    # True: señal real de /api/monitors (colector offline); False: heurística de respaldo
    confirmed: bool = False
    monitor_name: str = ""
    # Solo en outages heurísticos (confirmed=False): True si el colector está online igual
    # (posible problema de red/sitio), False si no tenemos el dato del colector.
    monitor_online: bool = False
