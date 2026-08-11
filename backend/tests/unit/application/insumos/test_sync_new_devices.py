"""Tests de SyncNewDevices — el diff del inventario de Insight contra known_devices."""

import pytest

from src.modules.insumos.application.use_cases.sync_new_devices import (
    SyncNewDevices,
    SyncNewDevicesPorts,
)
from src.shared.domain.errors import ExternalServiceError
from tests.unit.domain.insumos.fakes import (
    FakeCustomerConfigRepository,
    FakeInsightGateway,
    FakeKnownDeviceRepository,
)


def _device(device_id: int, serial: str = "SERIE1", **overrides: object) -> dict:
    base: dict[str, object] = {
        "deviceId": device_id,
        "serialNumber": serial,
        "ipAddress": "10.0.0.1",
        "monitorStatus": "N",
        "extendedFields": {"model": "HP E50145", "zone": "Sucursal"},
    }
    base.update(overrides)
    return base


class World:
    def __init__(self) -> None:
        self.insight = FakeInsightGateway()
        self.customers = FakeCustomerConfigRepository()
        self.devices = FakeKnownDeviceRepository()
        self.use_case = SyncNewDevices(
            SyncNewDevicesPorts(
                insight=self.insight,  # type: ignore[arg-type]
                customers=self.customers,  # type: ignore[arg-type]
                devices=self.devices,  # type: ignore[arg-type]
            )
        )

    def with_customer(self, customer_id: int, name: str = "Cliente Test") -> "World":
        self.insight.customers.append({"customerId": customer_id, "name": name})
        return self


async def test_los_clientes_nuevos_entran_deshabilitados() -> None:
    """Habilitar a un cliente lo mete en la auto-carga real: eso lo decide una
    persona, nunca un sync."""
    world = World().with_customer(8, "Sucursal Centro")

    await world.use_case.execute()

    assert world.customers.customers[0].enabled is False
    assert world.customers.customers[0].name == "Sucursal Centro"


async def test_devuelve_solo_los_equipos_vistos_por_primera_vez() -> None:
    world = World().with_customer(8)
    world.devices.add(1, customer_id=8)
    world.insight.inventory_by_customer[8] = [_device(1), _device(2)]

    result = await world.use_case.execute()

    assert result.new_device_ids == [2]


async def test_los_equipos_sin_serie_son_ruido_del_discovery_y_se_descartan() -> None:
    world = World().with_customer(8)
    world.insight.inventory_by_customer[8] = [_device(1, serial=""), _device(2)]

    result = await world.use_case.execute()

    assert result.new_device_ids == [2]


async def test_se_podan_los_equipos_que_insight_ya_no_devuelve() -> None:
    """Sin la poda quedaban huérfanos en Equipos Offline para siempre — el upsert
    nunca borra (bug real medido el 2026-07-31)."""
    world = World().with_customer(8)
    world.devices.add(1, customer_id=8)
    world.devices.add(2, customer_id=8)
    world.insight.inventory_by_customer[8] = [_device(1)]

    result = await world.use_case.execute()

    assert result.pruned == 1
    assert 2 not in world.devices.devices


async def test_un_cliente_que_falla_no_aborta_el_resto_ni_poda_sus_equipos() -> None:
    """Con un fetch fallido el inventario recibido no representa la realidad: podar
    con eso borraría equipos válidos por un error transitorio de red."""
    world = World().with_customer(8).with_customer(9)
    world.devices.add(1, customer_id=8)
    world.insight.inventory_errors[8] = ConnectionError("timeout")
    world.insight.inventory_by_customer[9] = [_device(50, serial="SERIE50")]

    result = await world.use_case.execute()

    assert result.pruned == 0
    assert 1 in world.devices.devices  # no se podó pese a no venir en el fetch
    assert result.new_device_ids == [50]  # el otro cliente sí se sincronizó
    assert [customer_id for customer_id, _ in world.devices.pruned] == [9]


async def test_si_insight_no_da_el_padron_el_sync_falla_explicito() -> None:
    """Sin clientes no hay a quién pedirle equipos: mejor un error que un sync vacío
    que "no encontró nada" y dispara la poda de todo."""
    world = World()
    world.insight.customers_error = ConnectionError("timeout")

    with pytest.raises(ExternalServiceError):
        await world.use_case.execute()

    assert world.devices.pruned == []


async def test_el_serial_se_normaliza_antes_de_guardarse() -> None:
    """Insight a veces devuelve el serial con punto final; CD hace match exacto."""
    world = World().with_customer(8)
    world.insight.inventory_by_customer[8] = [_device(1, serial="Z83DBJEJ90000GT. ")]

    await world.use_case.execute()

    assert world.devices.devices[1].serial == "Z83DBJEJ90000GT"
