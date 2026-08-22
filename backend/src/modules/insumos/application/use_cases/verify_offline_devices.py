"""Caso de uso VerifyOfflineDevices — clasifica equipos offline contra Canal Directo.

Secuencial y pausado a propósito (nunca gather/paralelo): wsAyC es el mismo webservice
frágil que Insight_Offline_Equipos audita a mano, cliente por cliente, con pausas de
3-4s entre serial y serial.

Flujo: lock → snapshot fresco → sync monitores → select_due → slice(limit) →
loop SOAP con asyncio.sleep(2.0) → un solo write con todos los resultados (incluidos
los ERROR) → summary con remaining.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.insumos.application.use_cases._offline_snapshot import (
    OfflineSnapshotPorts,
    build_offline_snapshot,
)
from src.modules.insumos.application.use_cases.sync_monitor_status import (
    SyncMonitorStatus,
    SyncMonitorStatusPorts,
)
from src.modules.insumos.domain.errors import OfflineCheckInProgressError
from src.modules.insumos.domain.repositories.exclusive_lock import ExclusiveLock
from src.modules.insumos.domain.repositories.known_device_repository import (
    KnownDeviceRepository,
)
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.services.machine_classification import classify_machine
from src.modules.insumos.domain.services.recheck_schedule import select_due
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings
from src.modules.insumos.domain.value_objects.offline_device import (
    CdVerdict,
    DeviceLocationUpdate,
    OfflineDevice,
)

logger = logging.getLogger(__name__)

VERIFY_DELAY_SECONDS = 2.0


@dataclass(frozen=True)
class VerifySummary:
    """Contador tipado — corrige el bug 1 del legacy: la clave inicializada era
    'errores' pero se incrementaba 'error', quedando siempre en 0."""

    checked: int = 0
    bodega: int = 0
    otro_cliente: int = 0
    en_cliente: int = 0
    errores: int = 0
    remaining: int = 0


@dataclass(frozen=True)
class VerifyOfflineDevicesPorts:
    snapshot: OfflineSnapshotPorts
    devices: KnownDeviceRepository
    wsayc: WsAycGateway
    verify_lock: ExclusiveLock
    sync_monitor_ports: SyncMonitorStatusPorts | None = None


class VerifyOfflineDevices:
    def __init__(self, ports: VerifyOfflineDevicesPorts, settings: InsumosSettings) -> None:
        self._ports = ports
        self._settings = settings

    async def execute(
        self,
        limit: int,
        customer_id: int | None = None,
    ) -> VerifySummary:
        """limit es obligatorio y acotado (le=50 en el router) para mantener la duración
        bajo control. Devuelve remaining para que la UI itere el lote."""
        async with self._ports.verify_lock.hold() as acquired:
            if not acquired:
                raise OfflineCheckInProgressError()
            return await self._run(limit, customer_id)

    async def _run(self, limit: int, customer_id: int | None) -> VerifySummary:
        await self._sync_monitors()
        snapshot = await build_offline_snapshot(self._ports.snapshot, self._settings)
        now = datetime.now(UTC)
        candidates = snapshot.devices
        if customer_id is not None:
            candidates = [d for d in candidates if d.customer_id == customer_id]
        due = select_due(candidates, snapshot.outage_device_ids, now)
        remaining = max(0, len(due) - limit)
        updates: list[DeviceLocationUpdate] = []
        for device in due[:limit]:
            updates.append(await self._check_one(device))
        if updates:
            await self._ports.devices.set_device_locations(updates)
        return _summarize(updates, remaining)

    async def _sync_monitors(self) -> None:
        """Refresca dca_monitors con el estado real de Insight antes del snapshot
        definitivo — solo si el wiring lo habilitó."""
        if self._ports.sync_monitor_ports is None:
            return
        snapshot = await build_offline_snapshot(self._ports.snapshot, self._settings)
        await SyncMonitorStatus(self._ports.sync_monitor_ports).execute(
            {d.customer_id for d in snapshot.devices}
        )

    async def _check_one(self, device: OfflineDevice) -> DeviceLocationUpdate:
        """Un getMachineBySerial + la pausa obligatoria; el error se persiste como ERROR."""
        try:
            machine = await self._ports.wsayc.get_machine_by_serial(device.serial)
            cd_status, cd_detail = classify_machine(machine, device.customer_name)
        except Exception as exc:
            logger.warning(
                "verify_offline: falló getMachineBySerial(%s) del equipo %d",
                device.serial,
                device.device_id,
                extra={"serial": device.serial, "device_id": device.device_id},
                exc_info=exc,
            )
            cd_status, cd_detail = CdVerdict.ERROR, "No se pudo consultar Canal Directo"
        await asyncio.sleep(VERIFY_DELAY_SECONDS)
        return DeviceLocationUpdate(device.device_id, cd_status, cd_detail)


def _count(updates: list[DeviceLocationUpdate], cd_status: str) -> int:
    return sum(1 for u in updates if u.cd_status == cd_status)


def _summarize(updates: list[DeviceLocationUpdate], remaining: int) -> VerifySummary:
    return VerifySummary(
        checked=len(updates),
        bodega=_count(updates, CdVerdict.BODEGA),
        otro_cliente=_count(updates, CdVerdict.OTRO_CLIENTE),
        en_cliente=_count(updates, CdVerdict.EN_CLIENTE),
        errores=_count(updates, CdVerdict.ERROR),
        remaining=remaining,
    )
