"""Puerto del padrón local de equipos vistos en Insight (tabla known_devices)."""

from typing import Protocol


class KnownDeviceRepository(Protocol):
    async def count_monitored_by_customer(self) -> dict[int, int]:
        """{customer_id: equipos con monitor_status = 'Y'}. Una sola query para todos
        los clientes — el detalle por cliente lo necesita de a uno, pero el poller y
        la detección de caída masiva lo necesitan completo."""
        ...
