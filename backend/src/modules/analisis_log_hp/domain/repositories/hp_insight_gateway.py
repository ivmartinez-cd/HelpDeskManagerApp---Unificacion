"""Puerto: HP Insight Portal API (autenticado con JWT).

Métodos que necesita el módulo analisis-log-hp — superconjunto de los que
insumos ya usa, pero implementado de forma independiente (ADR-018).
"""

from typing import Any, Protocol

JsonDict = dict[str, Any]


class HpInsightGateway(Protocol):
    async def search_by_serial(self, serial: str) -> JsonDict | None:
        """GET /api/devices/search?q=serial:{serial}. None si no existe."""
        ...

    async def get_device_consumables(self, device_id: int) -> list[JsonDict]: ...

    async def get_device_alerts_current(self, device_id: int) -> list[JsonDict]: ...

    async def get_device_alerts_history(
        self,
        device_id: int,
        from_date: str | None = None,
        to_date: str | None = None,
        max_results: int | None = None,
    ) -> list[JsonDict]: ...

    async def get_device_meters_history(
        self, device_id: int, days: int = 90
    ) -> list[JsonDict]: ...

    async def get_devices(self, customer_id: int) -> list[JsonDict]: ...
