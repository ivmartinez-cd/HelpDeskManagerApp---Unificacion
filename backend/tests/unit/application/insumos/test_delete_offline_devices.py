"""Tests de DeleteOfflineDevices — el motivo real (no genérico) de rechazo que se
loguea y viaja al frontend, y la secuencia completa por equipo (portal → auditoría →
borrado local) con sus variantes dry-run / rechazo / error del portal."""

from datetime import UTC, datetime

import pytest

from src.modules.insumos.application.use_cases.delete_offline_devices import (
    DeleteOfflineDevices,
    DeleteOfflineDevicesPorts,
)
from src.modules.insumos.domain.entities.audit_record import EVENT_DEVICE_DELETED
from src.modules.insumos.domain.errors import DeleteInProgressError
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings
from src.modules.insumos.domain.value_objects.offline_device import OfflineDevice
from tests.unit.application.insumos._offline_fakes import (
    FakeDcaMonitorRepository,
    FakeExclusiveLock,
    FakeOfflineDeviceRepository,
    FakeSdsPortalGateway,
    offline_device,
    snapshot_ports,
)
from tests.unit.domain.insumos.fakes import FakeOrderAuditRepository

_NOW = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)


def _device(device_id: int = 1, cd_status: str = "EN_CLIENTE") -> OfflineDevice:
    return OfflineDevice(
        device_id=device_id,
        customer_id=1,
        customer_name="Cliente",
        serial=f"SN{device_id}",
        model="HP LaserJet",
        zone="ZONA1",
        last_contact=_NOW,
        monitor_name="",
        cd_status=cd_status,
        cd_detail="",
        cd_checked_at=None,
        offline_dismissed=False,
    )


def test_equipo_ausente_del_snapshot() -> None:
    reason = DeleteOfflineDevices._rejection_reason(1, None, outage_device_ids=set())
    assert reason == "ya no está en el listado de equipos offline"


def test_equipo_en_caida_masiva() -> None:
    device = _device(1, cd_status="BODEGA")
    reason = DeleteOfflineDevices._rejection_reason(1, device, outage_device_ids={1})
    assert reason == "excluido por caída masiva de colector"


def test_equipo_fuera_de_bodega() -> None:
    device = _device(1, cd_status="EN_CLIENTE")
    reason = DeleteOfflineDevices._rejection_reason(1, device, outage_device_ids=set())
    assert reason == "cdStatus='EN_CLIENTE', esperado BODEGA"


# --- execute / _run: secuencia completa con fakes del flujo offline -------------------


class World:
    def __init__(self, *, dry_run: bool = False, acquired: bool = True) -> None:
        self.devices = FakeOfflineDeviceRepository()
        self.monitors = FakeDcaMonitorRepository()
        self.audit = FakeOrderAuditRepository()
        self.portal = FakeSdsPortalGateway()
        self.lock = FakeExclusiveLock(acquired)
        self.use_case = DeleteOfflineDevices(
            DeleteOfflineDevicesPorts(
                snapshot=snapshot_ports(self.devices, self.monitors),
                devices=self.devices,  # type: ignore[arg-type]
                audit=self.audit,
                portal=self.portal,
                delete_lock=self.lock,
            ),
            InsumosSettings(),
            dry_run=dry_run,
            tz=UTC,
        )


async def test_baja_real_borra_en_portal_audita_y_borra_local() -> None:
    world = World()
    world.devices.offline = [offline_device(1, cd_status="BODEGA", cd_detail="Sin asignar")]

    result = await world.use_case.execute([1])

    assert result.dry_run is False
    assert [(r.device_id, r.ok, r.error) for r in result.results] == [(1, True, None)]
    assert world.portal.deleted == [1]
    assert world.devices.deleted == [1]
    assert len(world.audit.records) == 1
    audit = world.audit.records[0]
    assert audit.event == EVENT_DEVICE_DELETED
    assert audit.device_id == 1
    assert audit.dry_run is False
    # Los días dependen del "hoy" real (last_contact fijo vs datetime.now).
    assert audit.detail is not None
    assert audit.detail.startswith("BODEGA · Sin asignar · ")
    assert audit.detail.endswith(" días offline")


async def test_dry_run_audita_pero_no_borra() -> None:
    world = World(dry_run=True)
    world.devices.offline = [offline_device(1, cd_status="BODEGA")]

    result = await world.use_case.execute([1])

    assert result.dry_run is True
    assert result.results[0].ok is True
    assert world.portal.deleted == []
    assert world.devices.deleted == []
    assert [a.dry_run for a in world.audit.records] == [True]


async def test_equipo_no_candidato_se_rechaza_con_motivo_y_no_toca_nada() -> None:
    world = World()
    world.devices.offline = [offline_device(1, cd_status="EN_CLIENTE")]

    result = await world.use_case.execute([1, 99])

    assert [r.ok for r in result.results] == [False, False]
    assert result.results[0].serial == "SERIE1"
    assert "cdStatus='EN_CLIENTE'" in (result.results[0].error or "")
    assert result.results[1].serial == ""
    assert "ya no está en el listado" in (result.results[1].error or "")
    assert world.portal.deleted == []
    assert world.audit.records == []


async def test_error_del_portal_marca_ok_false_y_sigue_con_el_resto() -> None:
    world = World()
    world.devices.offline = [
        offline_device(1, cd_status="BODEGA"),
        offline_device(2, cd_status="BODEGA"),
    ]
    world.portal.error = RuntimeError("portal caído")

    result = await world.use_case.execute([1, 2])

    assert [(r.device_id, r.ok, r.error) for r in result.results] == [
        (1, False, "portal caído"),
        (2, False, "portal caído"),
    ]
    assert world.devices.deleted == []
    assert world.audit.records == []


async def test_lock_tomado_por_otro_worker_rechaza() -> None:
    world = World(acquired=False)

    with pytest.raises(DeleteInProgressError):
        await world.use_case.execute([1])
