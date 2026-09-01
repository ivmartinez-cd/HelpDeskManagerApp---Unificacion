"""Caso de uso DeleteOfflineDevices — baja de equipos en BODEGA.

Estrictamente secuencial, nunca paralelo, nunca reintento por equipo.
Secuencia por equipo:
  (a) re-validar deletable server-side contra snapshot fresco — el frontend no es autoridad;
  (b) si no es dry-run: portal.delete_device() [irreversible];
  (c) SIEMPRE (incluso dry-run): auditar EVENT_DEVICE_DELETED con flag dry_run;
  (d) si no es dry-run: borrar la fila local.
Error en un equipo → ok=false, sigue con el resto.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, tzinfo

from src.modules.insumos.application.use_cases._offline_snapshot import (
    OfflineSnapshotPorts,
    build_offline_snapshot,
)
from src.modules.insumos.domain.entities.audit_record import EVENT_DEVICE_DELETED, AuditRecord
from src.modules.insumos.domain.errors import DeleteInProgressError
from src.modules.insumos.domain.repositories.known_device_repository import (
    KnownDeviceRepository,
)
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.repositories.sds_portal_gateway import SdsPortalGateway
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings
from src.modules.insumos.domain.value_objects.offline_clock import calendar_days_offline
from src.modules.insumos.domain.value_objects.offline_device import OfflineDevice
from src.shared.domain.repositories.exclusive_lock import ExclusiveLock

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeleteResult:
    device_id: int
    serial: str
    ok: bool
    error: str | None = None


@dataclass(frozen=True)
class DeleteOfflineDevicesResult:
    results: list[DeleteResult]
    dry_run: bool


@dataclass(frozen=True)
class DeleteOfflineDevicesPorts:
    snapshot: OfflineSnapshotPorts
    devices: KnownDeviceRepository
    audit: OrderAuditRepository
    portal: SdsPortalGateway
    delete_lock: ExclusiveLock


class DeleteOfflineDevices:
    def __init__(
        self,
        ports: DeleteOfflineDevicesPorts,
        settings: InsumosSettings,
        dry_run: bool,
        tz: tzinfo,
    ) -> None:
        self._ports = ports
        self._settings = settings
        self._dry_run = dry_run
        self._tz = tz

    async def execute(self, device_ids: list[int]) -> DeleteOfflineDevicesResult:
        async with self._ports.delete_lock.hold() as acquired:
            if not acquired:
                raise DeleteInProgressError()
            return await self._run(device_ids)

    async def _run(self, requested_ids: list[int]) -> DeleteOfflineDevicesResult:
        snapshot = await build_offline_snapshot(self._ports.snapshot, self._settings)
        by_id = {d.device_id: d for d in snapshot.devices}
        now = datetime.now(UTC)
        results: list[DeleteResult] = []
        for device_id in requested_ids:
            device = by_id.get(device_id)
            if device is None or device_id not in snapshot.deletable_ids:
                results.append(self._reject(device_id, device, snapshot.outage_device_ids))
            else:
                results.append(await self._delete_one(device, now))
        return DeleteOfflineDevicesResult(results=results, dry_run=self._dry_run)

    @classmethod
    def _reject(
        cls, device_id: int, device: OfflineDevice | None, outage_device_ids: set[int]
    ) -> DeleteResult:
        reason = cls._rejection_reason(device_id, device, outage_device_ids)
        serial = device.serial if device else ""
        logger.warning(
            "delete_offline: equipo %d rechazado, no es candidato válido (%s)",
            device_id,
            reason,
            extra={"device_id": device_id, "serial": serial, "reason": reason},
        )
        return DeleteResult(
            device_id=device_id,
            serial=serial,
            ok=False,
            error=f"El equipo no es un candidato válido para baja ({reason}).",
        )

    async def _delete_one(self, device: OfflineDevice, now: datetime) -> DeleteResult:
        """(b) portal → (c) auditoría (siempre) → (d) fila local; error → ok=False."""
        device_id = device.device_id
        try:
            if not self._dry_run:
                await self._ports.portal.delete_device(device_id)
            await self._ports.audit.record(self._build_audit(device, now))
            if not self._dry_run:
                await self._ports.devices.delete_device(device_id)
        except Exception as exc:
            logger.warning(
                "delete_offline: falló la baja del equipo %d (%s)",
                device_id,
                device.serial,
                extra={"device_id": device_id, "serial": device.serial},
                exc_info=exc,
            )
            return DeleteResult(device_id=device_id, serial=device.serial, ok=False, error=str(exc))
        return DeleteResult(device_id=device_id, serial=device.serial, ok=True)

    @staticmethod
    def _rejection_reason(
        device_id: int, device: OfflineDevice | None, outage_device_ids: set[int]
    ) -> str:
        """Motivo del rechazo, derivado del snapshot ya cargado — sin consultas extra."""
        if device is None:
            return "ya no está en el listado de equipos offline"
        if device_id in outage_device_ids:
            return "excluido por caída masiva de colector"
        return f"cdStatus={device.cd_status!r}, esperado BODEGA"

    def _build_audit(self, device: OfflineDevice, now: datetime) -> AuditRecord:
        days = calendar_days_offline(device.last_contact, now, self._tz)
        detail = (
            f"{device.cd_status} · {device.cd_detail} · "
            f"{days if days is not None else '?'} días offline"
        )
        return AuditRecord(
            event=EVENT_DEVICE_DELETED,
            customer_id=device.customer_id,
            customer_name=device.customer_name,
            device_serial=device.serial,
            device_id=device.device_id,
            detail=detail,
            dry_run=self._dry_run,
        )
