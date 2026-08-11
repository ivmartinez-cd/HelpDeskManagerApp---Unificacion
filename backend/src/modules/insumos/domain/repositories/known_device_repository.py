"""Puerto del padrón local de equipos vistos en Insight (tabla known_devices)."""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.entities.known_device import (
    DeviceInventoryEntry,
    KnownDevice,
)
from src.modules.insumos.domain.value_objects.offline_device import (
    DeviceLocationUpdate,
    OfflineDevice,
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

    async def list_offline(self, older_than_hours: int) -> list[OfflineDevice]:
        """Equipos cuyo last_contact tiene más de older_than_hours horas.

        LEFT JOIN a customer_config para traer el nombre del cliente. NO filtra
        por customers_config.enabled — ese flag gobierna la autocarga de pedidos,
        no el inventario (caso Santander: habilitado=False, 861 equipos offline
        que igual hay que auditar)."""
        ...

    async def set_device_locations(
        self, entries: Sequence[DeviceLocationUpdate]
    ) -> None:
        """Actualiza cd_status, cd_detail y cd_checked_at = now() para cada entry.

        cd_checked_at se pisa siempre, incluso si cd_status == ERROR: evita que el
        equipo queme el presupuesto del wsAyC en el lote siguiente sin esperar el
        intervalo de re-chequeo."""
        ...

    async def set_offline_dismissed(self, device_id: int, dismissed: bool) -> bool:
        """Marca/desmarca el equipo en la vista de Equipos Offline. Columna separada de
        `dismissed` (Equipos Sin Registrar) — son pantallas con criterios distintos.
        Devuelve False si el equipo no existe."""
        ...

    async def delete_device(self, device_id: int) -> bool:
        """Elimina el equipo del inventario local. Devuelve False si no existía.
        La baja en el PortalWeb (operación irreversible) ocurre antes — esta baja
        local es el paso final del flujo de delete_offline_devices."""
        ...
