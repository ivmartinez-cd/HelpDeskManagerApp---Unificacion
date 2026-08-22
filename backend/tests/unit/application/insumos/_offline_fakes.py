"""Fakes mínimos de los puertos del flujo de equipos offline (verify / delete).

Solo lo que usan build_offline_snapshot y los dos casos de uso de escritura; el resto
de KnownDeviceRepository queda en FakeKnownDeviceRepository (fakes de dominio).
"""

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from src.modules.insumos.application.use_cases._offline_snapshot import OfflineSnapshotPorts
from src.modules.insumos.domain.repositories.insight_gateway import JsonDict
from src.modules.insumos.domain.value_objects.dca_monitor import DcaMonitorStatus, MonitorKey
from src.modules.insumos.domain.value_objects.offline_device import (
    DeviceLocationUpdate,
    OfflineDevice,
)

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)


def offline_device(device_id: int = 1, **overrides: object) -> OfflineDevice:
    base: dict[str, object] = {
        "device_id": device_id,
        "customer_id": 8,
        "customer_name": "Cliente Test",
        "serial": f"SERIE{device_id}",
        "model": "HP E50145",
        "zone": "Sucursal",
        "last_contact": NOW,
        "monitor_name": "",
        "cd_status": "",
        "cd_detail": "",
        "cd_checked_at": None,
        "offline_dismissed": False,
    }
    base.update(overrides)
    return OfflineDevice(**base)  # type: ignore[arg-type]


class FakeOfflineDeviceRepository:
    """Solo los métodos de KnownDeviceRepository que toca el flujo offline."""

    def __init__(self, devices: list[OfflineDevice] | None = None) -> None:
        self.offline: list[OfflineDevice] = list(devices or [])
        self.location_updates: list[DeviceLocationUpdate] = []
        self.deleted: list[int] = []

    async def list_offline(self, older_than_hours: int) -> list[OfflineDevice]:
        return list(self.offline)

    async def count_monitored_by_customer(self) -> dict[int, int]:
        return {}

    async def set_device_locations(self, updates: Sequence[DeviceLocationUpdate]) -> None:
        self.location_updates.extend(updates)

    async def delete_device(self, device_id: int) -> bool:
        self.deleted.append(device_id)
        return True


class FakeDcaMonitorRepository:
    def __init__(self) -> None:
        self.upserted: list[DcaMonitorStatus] = []

    async def upsert(self, entries: Sequence[DcaMonitorStatus]) -> None:
        self.upserted.extend(entries)

    async def list_offline_monitors(self, stale_hours: int) -> set[MonitorKey]:
        return set()

    async def list_online_customer_ids(self) -> set[int]:
        return set()


class FakeExclusiveLock:
    def __init__(self, acquired: bool = True) -> None:
        self.acquired = acquired
        self.holds = 0

    @asynccontextmanager
    async def hold(self) -> AsyncIterator[bool]:
        self.holds += 1
        yield self.acquired


class FakeSdsPortalGateway:
    def __init__(self) -> None:
        self.deleted: list[int] = []
        self.error: Exception | None = None

    async def delete_device(self, device_id: int) -> None:
        if self.error is not None:
            raise self.error
        self.deleted.append(device_id)


class FakeMonitorInsight:
    """Solo get_monitors — lo único que usa SyncMonitorStatus."""

    def __init__(self) -> None:
        self.calls: list[int] = []

    async def get_monitors(self, customer_id: int) -> list[JsonDict]:
        self.calls.append(customer_id)
        return []


def snapshot_ports(
    devices: FakeOfflineDeviceRepository, monitors: FakeDcaMonitorRepository
) -> OfflineSnapshotPorts:
    return OfflineSnapshotPorts(devices=devices, monitors=monitors)  # type: ignore[arg-type]
