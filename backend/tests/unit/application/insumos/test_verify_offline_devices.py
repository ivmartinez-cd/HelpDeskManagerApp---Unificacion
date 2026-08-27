"""Tests de VerifyOfflineDevices — clasificación secuencial contra Canal Directo."""

from datetime import timedelta

import pytest

from src.modules.insumos.application.use_cases import verify_offline_devices as module
from src.modules.insumos.application.use_cases.sync_monitor_status import SyncMonitorStatusPorts
from src.modules.insumos.application.use_cases.verify_offline_devices import (
    VerifyOfflineDevices,
    VerifyOfflineDevicesPorts,
)
from src.modules.insumos.domain.errors import OfflineCheckInProgressError
from src.modules.insumos.domain.value_objects.cd_supply import CdMachine
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings
from tests.unit.application.insumos._offline_fakes import (
    NOW,
    FakeDcaMonitorRepository,
    FakeExclusiveLock,
    FakeMonitorInsight,
    FakeOfflineDeviceRepository,
    offline_device,
    snapshot_ports,
)
from tests.unit.domain.insumos.fakes import FakeWsAycGateway


class World:
    def __init__(self, *, acquired: bool = True, with_monitor_sync: bool = False) -> None:
        self.devices = FakeOfflineDeviceRepository()
        self.monitors = FakeDcaMonitorRepository()
        self.wsayc = FakeWsAycGateway()
        self.lock = FakeExclusiveLock(acquired)
        self.insight = FakeMonitorInsight()
        sync_ports = (
            SyncMonitorStatusPorts(insight=self.insight, monitors=self.monitors)  # type: ignore[arg-type]
            if with_monitor_sync
            else None
        )
        self.use_case = VerifyOfflineDevices(
            VerifyOfflineDevicesPorts(
                snapshot=snapshot_ports(self.devices, self.monitors),
                devices=self.devices,  # type: ignore[arg-type]
                wsayc=self.wsayc,
                verify_lock=self.lock,
                sync_monitor_ports=sync_ports,
            ),
            InsumosSettings(),
            reloj=lambda: NOW,
        )


@pytest.fixture(autouse=True)
def _sin_pausa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "VERIFY_DELAY_SECONDS", 0)


async def test_clasifica_bodega_y_persiste_en_un_solo_write() -> None:
    world = World()
    world.devices.offline = [offline_device(1), offline_device(2)]
    world.wsayc.machine = None  # SOAP sin asignación → BODEGA

    summary = await world.use_case.execute(limit=10)

    assert summary.checked == 2
    assert summary.bodega == 2
    assert summary.remaining == 0
    assert [(u.device_id, u.cd_status) for u in world.devices.location_updates] == [
        (1, "BODEGA"),
        (2, "BODEGA"),
    ]


async def test_limit_recorta_el_lote_y_reporta_remaining() -> None:
    world = World()
    world.devices.offline = [offline_device(1), offline_device(2), offline_device(3)]
    world.wsayc.machine = None

    summary = await world.use_case.execute(limit=2)

    assert summary.checked == 2
    assert summary.remaining == 1


async def test_error_del_soap_cuenta_como_error_y_sigue_con_el_resto() -> None:
    world = World()
    world.devices.offline = [offline_device(1)]
    world.wsayc.machine_error = RuntimeError("wsAyC caído")

    summary = await world.use_case.execute(limit=10)

    assert summary.checked == 1
    assert summary.errores == 1
    assert summary.bodega == 0
    update = world.devices.location_updates[0]
    assert update.cd_status == "ERROR"
    assert update.cd_detail == "No se pudo consultar Canal Directo"


async def test_en_cliente_y_otro_cliente_se_cuentan_por_separado() -> None:
    world = World()
    world.devices.offline = [
        offline_device(1, customer_name="Cliente Test"),
        offline_device(2, customer_name="Otra Empresa"),
    ]
    world.wsayc.machine = CdMachine(familia_id="255", empresa_name="Cliente Test")

    summary = await world.use_case.execute(limit=10)

    assert summary.en_cliente == 1
    assert summary.otro_cliente == 1


async def test_filtra_por_cliente_y_saltea_los_ya_verificados() -> None:
    world = World()
    world.devices.offline = [
        offline_device(1, customer_id=8),
        offline_device(2, customer_id=9),
        offline_device(3, customer_id=8, cd_status="BODEGA"),
        offline_device(4, customer_id=8, cd_status="EN_CLIENTE", cd_checked_at=NOW),
        offline_device(
            5, customer_id=8, cd_status="EN_CLIENTE", cd_checked_at=NOW - timedelta(days=30)
        ),
    ]
    world.wsayc.machine = None

    summary = await world.use_case.execute(limit=10, customer_id=8)

    assert [u.device_id for u in world.devices.location_updates] == [1, 5]
    assert summary.checked == 2


async def test_sin_equipos_no_escribe_nada() -> None:
    world = World()

    summary = await world.use_case.execute(limit=10)

    assert summary.checked == 0
    assert world.devices.location_updates == []


async def test_sincroniza_monitores_de_los_clientes_del_snapshot_antes_de_verificar() -> None:
    world = World(with_monitor_sync=True)
    world.devices.offline = [offline_device(1, customer_id=8), offline_device(2, customer_id=9)]
    world.wsayc.machine = None

    await world.use_case.execute(limit=10)

    assert sorted(world.insight.calls) == [8, 9]


async def test_lock_tomado_por_otro_worker_rechaza() -> None:
    world = World(acquired=False)

    with pytest.raises(OfflineCheckInProgressError):
        await world.use_case.execute(limit=10)
