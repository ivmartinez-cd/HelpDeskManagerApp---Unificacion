"""Tests de get_deletable_ids."""

from datetime import UTC, datetime

from src.modules.insumos.domain.services.offline_candidates import get_deletable_ids
from src.modules.insumos.domain.value_objects.offline_device import OfflineDevice

_NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)


def _device(
    device_id: int,
    cd_status: str,
    offline_dismissed: bool = False,
) -> OfflineDevice:
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
        offline_dismissed=offline_dismissed,
    )


def test_bodega_sin_outage_es_deletable() -> None:
    d = _device(1, cd_status="BODEGA")
    assert get_deletable_ids([d], outage_device_ids=set()) == [1]


def test_en_cliente_no_es_deletable() -> None:
    d = _device(1, cd_status="EN_CLIENTE")
    assert get_deletable_ids([d], outage_device_ids=set()) == []


def test_otro_cliente_no_es_deletable() -> None:
    d = _device(1, cd_status="OTRO_CLIENTE")
    assert get_deletable_ids([d], outage_device_ids=set()) == []


def test_bodega_en_outage_no_es_deletable() -> None:
    """BODEGA pero dentro de un outage detectado → no se ofrece para baja."""
    d = _device(1, cd_status="BODEGA")
    assert get_deletable_ids([d], outage_device_ids={1}) == []


def test_dismissed_no_afecta_deletable() -> None:
    """offline_dismissed=True no impide la baja — solo afecta la vista de la UI."""
    d = _device(1, cd_status="BODEGA", offline_dismissed=True)
    assert get_deletable_ids([d], outage_device_ids=set()) == [1]


def test_mezcla_de_estados() -> None:
    devices = [
        _device(1, cd_status="BODEGA"),
        _device(2, cd_status="EN_CLIENTE"),
        _device(3, cd_status="BODEGA"),  # en outage
        _device(4, cd_status="BODEGA", offline_dismissed=True),
    ]
    result = get_deletable_ids(devices, outage_device_ids={3})
    assert set(result) == {1, 4}
