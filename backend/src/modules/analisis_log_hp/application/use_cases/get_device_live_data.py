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


def _to_client_device(raw: dict[str, Any]) -> dict[str, Any]:
    """Traduce el dict crudo de Insight (`serialNumber`, `extendedFields.*`) al shape
    de dominio que espera el frontend (`device_id`, `serial`, `location`, `model`)."""
    extended = raw.get("extendedFields") or {}
    return {
        "device_id": raw.get("deviceId"),
        "serial": raw.get("serialNumber") or "",
        "location": extended.get("zone"),
        "model": extended.get("model"),
    }


def _to_client(raw: dict[str, Any]) -> dict[str, Any]:
    """`device_count` siempre 0: Insight no lo trae en la búsqueda de clientes y no
    hacemos un fan-out de `get_devices` por cliente solo para contar (N+1 lento)."""
    return {
        "customer_id": raw.get("customerId"),
        "name": raw.get("name") or raw.get("customerName") or "",
        "device_count": 0,
    }


class GetClientDevices:
    def __init__(self, insight: HpInsightGateway) -> None:
        self._insight = insight

    async def execute(self, customer_id: int) -> list[dict[str, Any]]:
        raw = await self._insight.get_devices(customer_id)
        return [_to_client_device(d) for d in raw]


class GetClients:
    def __init__(self, insight: HpInsightGateway) -> None:
        self._insight = insight

    async def execute(self) -> list[dict[str, Any]]:
        raw = await self._insight.get_customers()
        return [_to_client(c) for c in raw]
