"""Casos de uso: consumibles, alertas y metros de un equipo vía Insight."""

from __future__ import annotations

from typing import Any

from src.modules.analisis_log_hp.domain.repositories.hp_insight_gateway import HpInsightGateway


class GetDeviceConsumables:
    def __init__(self, insight: HpInsightGateway) -> None:
        self._insight = insight

    async def execute(self, device_id: int) -> list[dict[str, Any]]:
        return await self._insight.get_device_consumables(device_id)


class GetDeviceAlerts:
    def __init__(self, insight: HpInsightGateway) -> None:
        self._insight = insight

    async def execute(
        self,
        device_id: int,
        *,
        current_only: bool = True,
        from_date: str | None = None,
        to_date: str | None = None,
        max_results: int | None = None,
    ) -> list[dict[str, Any]]:
        if current_only:
            return await self._insight.get_device_alerts_current(device_id)
        return await self._insight.get_device_alerts_history(
            device_id, from_date=from_date, to_date=to_date, max_results=max_results
        )


class GetDeviceMeters:
    def __init__(self, insight: HpInsightGateway) -> None:
        self._insight = insight

    async def execute(self, device_id: int, days: int = 90) -> list[dict[str, Any]]:
        return await self._insight.get_device_meters_history(device_id, days=days)


class GetFleetClients:
    def __init__(self, insight: HpInsightGateway) -> None:
        self._insight = insight

    async def execute(self) -> list[dict[str, Any]]:
        return await self._insight.get_customers()


class GetClientDevices:
    def __init__(self, insight: HpInsightGateway) -> None:
        self._insight = insight

    async def execute(self, customer_id: int) -> list[dict[str, Any]]:
        return await self._insight.get_devices(customer_id)
