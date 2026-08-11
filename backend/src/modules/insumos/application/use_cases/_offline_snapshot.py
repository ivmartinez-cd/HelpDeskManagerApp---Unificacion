"""Snapshot de equipos offline — núcleo compartido por todos los endpoints de offline.

Las 4 queries locales + la detección de caídas ocurren aquí. Cero red: no llama ni
a Insight ni al SOAP. El snapshot se construye una vez por request y lo reutilizan
todos los casos de uso de lectura (ListOfflineDevices, ListOfflineOutages,
CountOfflineCandidates) y los de escritura (verify, delete).
"""

import asyncio
from dataclasses import dataclass

from src.modules.insumos.domain.repositories.dca_monitor_repository import DcaMonitorRepository
from src.modules.insumos.domain.repositories.known_device_repository import (
    KnownDeviceRepository,
)
from src.modules.insumos.domain.services.offline_candidates import get_deletable_ids
from src.modules.insumos.domain.services.outage_detection import detect_outages
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings
from src.modules.insumos.domain.value_objects.offline_device import MassOutage, OfflineDevice


@dataclass(frozen=True)
class OfflineSnapshotPorts:
    devices: KnownDeviceRepository
    monitors: DcaMonitorRepository


@dataclass(frozen=True)
class OfflineSnapshot:
    devices: list[OfflineDevice]
    outages: list[MassOutage]
    outage_device_ids: set[int]
    deletable_ids: list[int]


async def build_offline_snapshot(
    ports: OfflineSnapshotPorts,
    settings: InsumosSettings,
) -> OfflineSnapshot:
    """Las 4 queries locales corren en paralelo — son independientes entre sí."""
    devices, fleet_sizes, offline_monitor_keys, online_customer_ids = await asyncio.gather(
        ports.devices.list_offline(settings.offline_device_hours),
        ports.devices.count_monitored_by_customer(),
        # Bug 2 del legacy corregido: siempre offline_monitor_hours (48), nunca
        # offline_device_hours (72). El job nocturno legacy caía al valor equivocado.
        ports.monitors.list_offline_monitors(settings.offline_monitor_hours),
        ports.monitors.list_online_customer_ids(),
    )
    outages = detect_outages(
        devices,
        fleet_sizes,
        offline_monitor_keys,
        min_devices=settings.offline_outage_min_devices,
        online_customer_ids=online_customer_ids,
        min_percent=settings.offline_outage_min_percent,
    )
    outage_device_ids = {did for o in outages for did in o.device_ids}
    deletable_ids = get_deletable_ids(devices, outage_device_ids)
    return OfflineSnapshot(
        devices=devices,
        outages=outages,
        outage_device_ids=outage_device_ids,
        deletable_ids=deletable_ids,
    )
