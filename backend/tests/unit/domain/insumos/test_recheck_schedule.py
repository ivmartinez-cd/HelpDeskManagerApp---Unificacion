"""Tests de select_due — selección de equipos offline pendientes de re-verificación."""

from datetime import UTC, datetime, timedelta

from src.modules.insumos.domain.services.recheck_schedule import (
    RECHECK_INTERVAL_DAYS,
    select_due,
)
from src.modules.insumos.domain.value_objects.offline_device import OfflineDevice

_NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
_OLD_CHECK = _NOW - timedelta(days=RECHECK_INTERVAL_DAYS + 1)
_RECENT_CHECK = _NOW - timedelta(days=1)


def _device(
    device_id: int,
    cd_status: str = "",
    cd_checked_at: datetime | None = None,
    offline_dismissed: bool = False,
    last_contact: datetime | None = None,
) -> OfflineDevice:
    return OfflineDevice(
        device_id=device_id,
        customer_id=1,
        customer_name="Cliente",
        serial=f"SN{device_id}",
        model="HP LaserJet",
        zone="ZONA1",
        last_contact=last_contact or _NOW - timedelta(days=5),
        monitor_name="",
        cd_status=cd_status,
        cd_detail="",
        cd_checked_at=cd_checked_at,
        offline_dismissed=offline_dismissed,
    )


def test_incluye_sin_verificacion_previa() -> None:
    d = _device(1, cd_status="", cd_checked_at=None)
    result = select_due([d], outage_device_ids=set(), now=_NOW)
    assert len(result) == 1


def test_incluye_verificacion_vencida() -> None:
    d = _device(1, cd_status="OTRO_CLIENTE", cd_checked_at=_OLD_CHECK)
    result = select_due([d], outage_device_ids=set(), now=_NOW)
    assert len(result) == 1


def test_excluye_bodega() -> None:
    """BODEGA ya está confirmado; no hace falta re-chequear."""
    d = _device(1, cd_status="BODEGA", cd_checked_at=None)
    result = select_due([d], outage_device_ids=set(), now=_NOW)
    assert result == []


def test_excluye_miembro_de_outage() -> None:
    d = _device(1, cd_status="", cd_checked_at=None)
    result = select_due([d], outage_device_ids={1}, now=_NOW)
    assert result == []


def test_excluye_verificacion_reciente() -> None:
    d = _device(1, cd_status="EN_CLIENTE", cd_checked_at=_RECENT_CHECK)
    result = select_due([d], outage_device_ids=set(), now=_NOW)
    assert result == []


def test_no_filtra_offline_dismissed() -> None:
    """dismissed=True no excluye del re-chequeo — hay que mantener el estado actualizado."""
    d = _device(1, cd_status="", cd_checked_at=None, offline_dismissed=True)
    result = select_due([d], outage_device_ids=set(), now=_NOW)
    assert len(result) == 1


def test_orden_last_contact_asc() -> None:
    """Los equipos más antiguos van primero."""
    d_nuevo = _device(1, last_contact=_NOW - timedelta(days=3))
    d_viejo = _device(2, last_contact=_NOW - timedelta(days=10))
    result = select_due([d_nuevo, d_viejo], outage_device_ids=set(), now=_NOW)
    assert result[0].device_id == 2
    assert result[1].device_id == 1
