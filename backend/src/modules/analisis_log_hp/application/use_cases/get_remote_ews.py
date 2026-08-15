"""Caso de uso: obtener link temporal EWS remoto de un equipo HP."""

from __future__ import annotations

from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import HpPortalGateway


class GetRemoteEws:
    def __init__(self, portal: HpPortalGateway) -> None:
        self._portal = portal

    async def execute(self, device_id: str) -> str | None:
        return await self._portal.fetch_remote_ews_url(device_id)
