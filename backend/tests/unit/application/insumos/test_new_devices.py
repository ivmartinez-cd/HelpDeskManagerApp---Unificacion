"""Tests de la pantalla de equipos sin registrar (listado, badge y descarte)."""

from src.modules.insumos.application.use_cases.list_new_devices import (
    CountNewDevices,
    DismissNewDevice,
    ListNewDevices,
    NewDevicesPorts,
)
from tests.unit.domain.insumos.fakes import FakeKnownDeviceRepository

INSIGHT_BASE = "https://sds.example.com/PortalAPI"


class World:
    def __init__(self) -> None:
        self.devices = FakeKnownDeviceRepository()
        ports = NewDevicesPorts(devices=self.devices)  # type: ignore[arg-type]
        self.list = ListNewDevices(ports, INSIGHT_BASE)
        self.count = CountNewDevices(ports)
        self.dismiss = DismissNewDevice(ports)


async def test_los_equipos_ya_monitoreados_no_aparecen() -> None:
    """'Y' (monitoreado) y 'J' (en alta) ya generan avisos de insumos: no hay nada que
    registrar."""
    world = World()
    world.devices.add(1, monitor_status="N")
    world.devices.add(2, monitor_status="Y")
    world.devices.add(3, monitor_status="J")

    rows = await world.list.execute()

    assert [r.device.device_id for r in rows] == [1]


async def test_los_equipos_de_clientes_deshabilitados_no_aparecen() -> None:
    world = World()
    world.devices.add(1)
    world.devices.add(2, customer_id=99)
    world.devices.enabled_customers.discard(99)

    rows = await world.list.execute()

    assert [r.device.device_id for r in rows] == [1]


async def test_el_link_de_registro_apunta_al_portalweb_no_a_la_api() -> None:
    world = World()
    world.devices.add(77)

    rows = await world.list.execute()

    assert rows[0].registration_url == (
        "https://sds.example.com/PortalWeb/asset-registration?step=1&action=edit&d=77"
    )


async def test_los_ignorados_se_listan_pero_no_cuentan_para_el_badge() -> None:
    """La UI los muestra tachados; el badge cuenta lo que hay para hacer."""
    world = World()
    world.devices.add(1)
    world.devices.add(2, dismissed=True)

    rows = await world.list.execute()

    assert len(rows) == 2
    assert await world.count.execute() == 1


async def test_descartar_un_equipo_lo_saca_del_badge() -> None:
    world = World()
    world.devices.add(1)

    assert await world.dismiss.execute(1, dismissed=True) is True
    assert await world.count.execute() == 0


async def test_descartar_un_equipo_inexistente_avisa_en_vez_de_fingir_exito() -> None:
    world = World()

    assert await world.dismiss.execute(404, dismissed=True) is False
