"""Puerto del padrón local de equipos vistos en Insight (tabla known_devices)."""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.entities.known_device import (
    DeviceInventoryEntry,
    KnownDevice,
)


class KnownDeviceRepository(Protocol):
    async def count_monitored_by_customer(self) -> dict[int, int]:
        """{customer_id: equipos con monitor_status = 'Y'}. Una sola query para todos
        los clientes — el detalle por cliente lo necesita de a uno, pero el poller y
        la detección de caída masiva lo necesitan completo."""
        ...

    async def list_pending(self) -> list[KnownDevice]:
        """Equipos sin registrar de clientes habilitados, más nuevo primero. Incluye
        los ignorados: la UI los muestra tachados, no los esconde."""
        ...

    async def count_pending(self) -> int:
        """Igual que list_pending pero excluyendo los ignorados — es el número del
        badge, que cuenta lo que hay para hacer, no lo que hay para mirar."""
        ...

    async def set_dismissed(self, device_id: int, dismissed: bool) -> bool:
        """Marca/desmarca "ignorado" en la pantalla de equipos sin registrar. False si
        el equipo no existe. Columna separada de la de Equipos Offline a propósito —
        son dos pantallas distintas con criterios distintos."""
        ...

    async def upsert(self, entries: Sequence[DeviceInventoryEntry]) -> list[int]:
        """Sincroniza el inventario y devuelve los device_id vistos por primera vez.

        El upsert refresca el estado actual: cuando alguien registra el equipo en SDS
        su monitor_status pasa a 'Y' y sale solo de la lista de pendientes. Si cambió
        `last_contact` (el equipo volvió a reportar) se limpia el veredicto de la
        auditoría de offline, que quedó obsoleto."""
        ...

    async def prune_missing(
        self, customer_id: int, present_device_ids: Sequence[int]
    ) -> int:
        """Borra los equipos de ese cliente que Insight ya no devuelve (dados de baja
        en SDS por fuera de esta app) y devuelve cuántos. Llamarla SOLO con un fetch
        completo y exitoso: con uno parcial podaría equipos válidos por un error
        transitorio de red. Sin esto quedaban huérfanos para siempre en Equipos
        Offline — medido en producción el 2026-07-31."""
        ...
