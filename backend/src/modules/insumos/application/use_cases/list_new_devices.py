"""Casos de uso de lectura de equipos sin registrar — port de routers/new_devices.py.

Leen solo el estado local (known_devices), sin llamadas de red: el inventario lo
refresca el sync (ver SyncNewDevices) o el poller. Un equipo sale de la lista solo
cuando alguien lo registra en el portal de SDS y su monitor_status pasa a 'Y'.
"""

from dataclasses import dataclass

from src.modules.insumos.application.dtos.new_devices import NewDeviceRow
from src.modules.insumos.domain.repositories.known_device_repository import (
    KnownDeviceRepository,
)
from src.modules.insumos.domain.value_objects.portal_urls import device_registration_url


@dataclass(frozen=True)
class NewDevicesPorts:
    devices: KnownDeviceRepository


class ListNewDevices:
    def __init__(self, ports: NewDevicesPorts, insight_base_url: str) -> None:
        self._ports = ports
        self._insight_base_url = insight_base_url

    async def execute(self) -> list[NewDeviceRow]:
        """Equipos descubiertos en SDS y todavía sin monitorear (no generan avisos de
        insumos), incluidos los ignorados — la UI los muestra, no los esconde."""
        return [
            NewDeviceRow(
                device=device,
                registration_url=device_registration_url(
                    self._insight_base_url, device.device_id
                ),
            )
            for device in await self._ports.devices.list_pending()
        ]


class CountNewDevices:
    def __init__(self, ports: NewDevicesPorts) -> None:
        self._ports = ports

    async def execute(self) -> int:
        """Solo el contador de pendientes sin ignorar — el badge de la barra lateral,
        que no puede pagar el listado completo en cada navegación."""
        return await self._ports.devices.count_pending()


class DismissNewDevice:
    def __init__(self, ports: NewDevicesPorts) -> None:
        self._ports = ports

    async def execute(self, device_id: int, dismissed: bool) -> bool:
        """Marca/desmarca un equipo como ignorado (p.ej. fuera de contrato). False si
        el equipo no existe."""
        return await self._ports.devices.set_dismissed(device_id, dismissed)
