"""Caso de uso: disparar actualización de caché HP en el portal SDS."""

from __future__ import annotations

from typing import Any

from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import HpPortalGateway


class RefreshHpCache:
    def __init__(self, portal: HpPortalGateway) -> None:
        self._portal = portal

    async def execute(self, device_id: str) -> list[dict[str, Any]]:
        """Devuelve las operaciones baseline (pre-refresh) de las acciones de caché."""
        return await self._portal.refresh_hp_cache(device_id)
