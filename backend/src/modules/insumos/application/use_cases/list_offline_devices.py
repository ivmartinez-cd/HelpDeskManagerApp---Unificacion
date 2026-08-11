"""Casos de uso de lectura de equipos offline y caídas de colector.

Todos comparten el snapshot local — cero red (no Insight, no SOAP). El estado de
cada equipo lo refresca VerifyOfflineDevices (paso 6).
"""

from dataclasses import dataclass

from src.modules.insumos.application.use_cases._offline_snapshot import (
    OfflineSnapshot,
    OfflineSnapshotPorts,
    build_offline_snapshot,
)
from src.modules.insumos.domain.repositories.known_device_repository import (
    KnownDeviceRepository,
)
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings
from src.modules.insumos.domain.value_objects.offline_device import MassOutage, OfflineDevice


@dataclass(frozen=True)
class OfflineDevicesPorts:
    devices: KnownDeviceRepository
    snapshot: OfflineSnapshotPorts


class ListOfflineDevices:
    def __init__(self, ports: OfflineSnapshotPorts, settings: InsumosSettings) -> None:
        self._ports = ports
        self._settings = settings

    async def execute(
        self, customer_id: int | None = None
    ) -> tuple[list[OfflineDevice], OfflineSnapshot]:
        snapshot = await build_offline_snapshot(self._ports, self._settings)
        devices = snapshot.devices
        if customer_id is not None:
            devices = [d for d in devices if d.customer_id == customer_id]
        return devices, snapshot


class ListOfflineOutages:
    def __init__(self, ports: OfflineSnapshotPorts, settings: InsumosSettings) -> None:
        self._ports = ports
        self._settings = settings

    async def execute(self) -> list[MassOutage]:
        snapshot = await build_offline_snapshot(self._ports, self._settings)
        return snapshot.outages


class CountOfflineCandidates:
    def __init__(self, ports: OfflineSnapshotPorts, settings: InsumosSettings) -> None:
        self._ports = ports
        self._settings = settings

    async def execute(self) -> int:
        """Cuenta de equipos en BODEGA sin outage — candidatos a baja masiva.

        No se puede resolver con COUNT en SQL: `deletable` depende de la detección
        de caídas (doble umbral, señal de colectores). Expresarlo en SQL duplicaría
        lógica de negocio en infraestructura."""
        snapshot = await build_offline_snapshot(self._ports, self._settings)
        return len(snapshot.deletable_ids)


class DismissOfflineDevice:
    def __init__(self, ports: OfflineSnapshotPorts) -> None:
        self._devices = ports.devices

    async def execute(self, device_id: int, dismissed: bool) -> bool:
        """Marca/desmarca el equipo en la vista offline. False si no existe."""
        return await self._devices.set_offline_dismissed(device_id, dismissed)
