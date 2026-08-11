"""Caso de uso GetInsumosConfig — port de GET /api/config (routers/config.py).

Las keys que no estén en app_settings caen en el default del dominio, y un valor
corrupto también (settings_from_raw loguea y usa el default) — la pantalla de
configuración nunca queda sin poder abrirse por un valor mal grabado.
"""

from dataclasses import dataclass

from src.modules.insumos.application.dtos.insumos_config import ConfigView
from src.modules.insumos.domain.repositories.insumos_settings_repository import (
    InsumosSettingsRepository,
)
from src.modules.insumos.domain.value_objects.insumos_settings import (
    logistics_recipients,
    settings_from_raw,
)


@dataclass(frozen=True)
class GetInsumosConfigPorts:
    settings: InsumosSettingsRepository


class GetInsumosConfig:
    def __init__(self, ports: GetInsumosConfigPorts) -> None:
        self._ports = ports

    async def execute(self) -> ConfigView:
        settings = settings_from_raw(await self._ports.settings.get_all())
        return ConfigView(
            settings=settings, logistics_mail_to=logistics_recipients(settings)
        )
