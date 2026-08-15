"""Caso de uso: resolver datos de un equipo por número de serie vía Insight API."""

from __future__ import annotations

from typing import Any

from src.modules.analisis_log_hp.domain.repositories.hp_insight_gateway import HpInsightGateway


class ResolveDevice:
    def __init__(self, insight: HpInsightGateway) -> None:
        self._insight = insight

    async def execute(self, serial: str) -> dict[str, Any] | None:
        return await self._insight.search_by_serial(serial.strip().upper())
