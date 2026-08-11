"""Identificación de equipos candidatos a baja."""

from src.modules.insumos.domain.value_objects.offline_device import OfflineDevice


def get_deletable_ids(
    devices: list[OfflineDevice],
    outage_device_ids: set[int],
) -> list[int]:
    """IDs de equipos habilitados para baja: no en outage y cd_status == BODEGA.

    offline_dismissed NO afecta deletable — solo el contador de la UI. Un equipo
    descartado de la vista sigue siendo candidato a baja si está en BODEGA.
    """
    return [
        d.device_id
        for d in devices
        if d.device_id not in outage_device_ids and d.cd_status == "BODEGA"
    ]
