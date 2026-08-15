"""Caso de uso: obtener tabla de operaciones HP Smart del portal SDS."""

from __future__ import annotations

from typing import Any

from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import HpPortalGateway


class GetHpOperations:
    def __init__(self, portal: HpPortalGateway) -> None:
        self._portal = portal

    async def execute(self, device_id: str) -> list[dict[str, Any]]:
        return await self._portal.get_hp_operations(device_id)
