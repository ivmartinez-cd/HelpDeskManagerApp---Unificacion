"""Selección de equipos offline pendientes de re-verificación contra Canal Directo."""

from datetime import UTC, datetime, timedelta

from src.modules.insumos.domain.value_objects.offline_device import OfflineDevice

RECHECK_INTERVAL_DAYS = 7


def select_due(
    devices: list[OfflineDevice],
    outage_device_ids: set[int],
    now: datetime,
) -> list[OfflineDevice]:
    """Equipos que corresponde (re)chequear en este ciclo de verify.

    Tres condiciones en AND:
    1. No pertenece a un outage detectado (ni confirmado ni heurístico).
    2. cd_status != BODEGA (ya confirmado en bodega, no hace falta repetir).
    3. Sin verificación previa, o la última fue hace más de RECHECK_INTERVAL_DAYS.

    offline_dismissed no filtra: hay que mantener el estado del equipo actualizado aunque
    el operador lo haya descartado de la vista (podría volver a habilitarlo).

    Orden: last_contact ASC (los más viejos primero).
    """
    cutoff = now - timedelta(days=RECHECK_INTERVAL_DAYS)
    due = [
        d
        for d in devices
        if d.device_id not in outage_device_ids
        and d.cd_status != "BODEGA"
        and (d.cd_checked_at is None or d.cd_checked_at.astimezone(UTC) < cutoff)
    ]
    due.sort(key=lambda d: (d.last_contact is None, d.last_contact))
    return due
