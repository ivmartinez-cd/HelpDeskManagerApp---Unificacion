"""Tests de DeleteOfflineDevices._rejection_reason — el motivo real (no genérico) que
se loguea y viaja al frontend cuando un equipo pedido para baja no es candidato válido.

Los otros caminos del use case (éxito, dry-run, fallo de baja contra el portal) no tienen
fakes de DcaMonitorRepository/SdsPortalGateway/ExclusiveLock en el repo todavía — deuda de
tests pre-existente, no introducida acá. _rejection_reason es un staticmethod puro,
testeable sin construir el use case completo."""

from datetime import UTC, datetime

from src.modules.insumos.application.use_cases.delete_offline_devices import (
    DeleteOfflineDevices,
)
from src.modules.insumos.domain.value_objects.offline_device import OfflineDevice

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
