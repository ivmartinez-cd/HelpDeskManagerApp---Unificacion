"""Tests de detect_monitor_outages, detect_mass_outages y detect_outages."""

from datetime import UTC, datetime

from src.modules.insumos.domain.services.outage_detection import (
    detect_mass_outages,
    detect_monitor_outages,
    detect_outages,
)
from src.modules.insumos.domain.value_objects.dca_monitor import MonitorKey
from src.modules.insumos.domain.value_objects.offline_device import OfflineDevice


def _device(
    device_id: int,
    customer_id: int,
    monitor_name: str = "",
    last_contact: datetime | None = None,
    customer_name: str = "Cliente",
    cd_status: str = "",
) -> OfflineDevice:
    lc = last_contact or datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    return OfflineDevice(
        device_id=device_id,
        customer_id=customer_id,
        customer_name=customer_name,
        serial=f"SN{device_id}",
        model="HP LaserJet",
        zone="ZONA1",
        last_contact=lc,
        monitor_name=monitor_name,
        cd_status=cd_status,
        cd_detail="",
        cd_checked_at=None,
        offline_dismissed=False,
    )


# ------ detect_monitor_outages ------


def test_monitor_outage_bug3_colectores_homonimos_no_se_contaminan() -> None:
    """Bug 3 del legacy: dos clientes con colector del mismo nombre, uno caído.
    Solo los equipos del cliente con el colector offline deben quedar en outage."""
    devices = [
        _device(1, customer_id=10, monitor_name="SDS-MONITOR"),
        _device(2, customer_id=10, monitor_name="SDS-MONITOR"),
        _device(3, customer_id=20, monitor_name="SDS-MONITOR"),  # otro cliente
    ]
    # Solo el colector del cliente 10 está offline
    offline_keys = {MonitorKey(10, "SDS-MONITOR")}

    outages = detect_monitor_outages(devices, offline_keys)

    assert len(outages) == 1
    assert outages[0].customer_id == 10
    assert set(outages[0].device_ids) == {1, 2}


def test_monitor_outage_sin_umbral_de_cantidad() -> None:
    """La señal real de colector no tiene umbral mínimo de dispositivos."""
    devices = [_device(1, customer_id=10, monitor_name="SDS-MON")]
    offline_keys = {MonitorKey(10, "SDS-MON")}

    outages = detect_monitor_outages(devices, offline_keys)

    assert len(outages) == 1
    assert outages[0].confirmed is True


def test_monitor_outage_vacio_si_no_hay_claves() -> None:
    devices = [_device(1, customer_id=10, monitor_name="SDS-MON")]
    outages = detect_monitor_outages(devices, set())
    assert outages == []


def test_monitor_outage_day_es_minimo_de_last_contact() -> None:
    """day es el mínimo de last_contact del grupo (el más antiguo), no el mayor."""
    d1 = _device(1, 10, "MON", last_contact=datetime(2026, 7, 3, 12, 0, tzinfo=UTC))
    d2 = _device(2, 10, "MON", last_contact=datetime(2026, 7, 1, 8, 0, tzinfo=UTC))
    offline_keys = {MonitorKey(10, "MON")}

    outages = detect_monitor_outages([d1, d2], offline_keys)

    assert outages[0].day == "2026-07-01"


# ------ detect_mass_outages ------


def test_mass_outage_division_float_umbral_porcentaje() -> None:
    """5/48 = 10.41% pasa el umbral de 10% — debe ser división float, no entera."""
    devices = [_device(i, customer_id=10) for i in range(5)]
    fleet_sizes = {10: 48}

    outages = detect_mass_outages(devices, fleet_sizes, min_devices=5, min_percent=10)

    assert len(outages) == 1


def test_mass_outage_fleet_cero_saltea_chequeo_de_porcentaje() -> None:
    """Si fleet_size == 0 no conocemos la flota; se omite el chequeo de %."""
    devices = [_device(i, customer_id=10) for i in range(5)]
    fleet_sizes: dict[int, int] = {}  # sin dato de flota

    outages = detect_mass_outages(devices, fleet_sizes, min_devices=5, min_percent=99)

    assert len(outages) == 1


def test_mass_outage_no_llega_minimo_de_dispositivos() -> None:
    devices = [_device(1, customer_id=10), _device(2, customer_id=10)]
    outages = detect_mass_outages(devices, {}, min_devices=5)
    assert outages == []


def test_mass_outage_no_llega_porcentaje_minimo() -> None:
    """5/100 = 5% no pasa el umbral de 10%."""
    # 5 devices min, fleet 100 → 5/100 = 5% < 10%
    devices_5 = [_device(i, customer_id=10) for i in range(5)]
    fleet_sizes = {10: 100}

    outages = detect_mass_outages(devices_5, fleet_sizes, min_devices=5, min_percent=10)

    assert outages == []


# ------ detect_outages ------


def test_detect_outages_concatena_sin_re_sort_global() -> None:
    """monitor_outages se concatenan primero; no hay re-sort que mezcle las dos señales."""
    # 1 equipo con colector offline, 5 equipos en mass outage (otro cliente)
    monitor_device = _device(1, customer_id=10, monitor_name="MON")
    mass_devices = [_device(i + 10, customer_id=20) for i in range(5)]
    devices = [monitor_device] + mass_devices
    offline_keys = {MonitorKey(10, "MON")}
    fleet_sizes: dict[int, int] = {}

    outages = detect_outages(devices, fleet_sizes, offline_keys, min_devices=5)

    # El de monitor (1 device) va primero, aunque tiene menos que el mass (5 devices)
    assert outages[0].confirmed is True
    assert outages[1].confirmed is False


def test_detect_outages_excluye_dispositivos_del_monitor_de_heuristica() -> None:
    """Los devices bajo el colector offline no se cuentan dos veces en detect_mass_outages."""
    shared_day = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    # 10 devices del mismo cliente, de los cuales 3 tienen el colector offline
    monitor_devices = [
        _device(i, customer_id=10, monitor_name="MON", last_contact=shared_day)
        for i in range(3)
    ]
    other_devices = [
        _device(i + 3, customer_id=10, monitor_name="", last_contact=shared_day)
        for i in range(3)
    ]
    devices = monitor_devices + other_devices
    offline_keys = {MonitorKey(10, "MON")}
    # fleet_sizes vacío → fleet=0 → no chequea %
    fleet_sizes: dict[int, int] = {}

    outages = detect_outages(devices, fleet_sizes, offline_keys, min_devices=10)

    # Los 3 del monitor van a monitor_outages; los 3 restantes no llegan a min_devices=10
    assert len(outages) == 1
    assert outages[0].confirmed is True
