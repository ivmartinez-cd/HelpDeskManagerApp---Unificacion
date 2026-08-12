"""Caso de uso SaveInsumosConfig — port de PUT /api/config (routers/config.py).

Se persiste todo o nada: si alguna validación falla no se graba ninguna key, para no
dejar la configuración a medio aplicar (p.ej. umbrales incoherentes entre sí).

Fuera de alcance a propósito: `maybe_auto_load`, que comparte archivo con estos dos
endpoints en el legacy pero es lógica del poller de fondo, no de configuración.
"""

from dataclasses import dataclass, replace

from src.modules.insumos.application.dtos.insumos_config import (
    SaveConfigCommand,
    SaveConfigResult,
)
from src.modules.insumos.domain.repositories.insumos_settings_repository import (
    InsumosSettingsRepository,
)
from src.modules.insumos.domain.services.settings_validation import validate_settings
from src.modules.insumos.domain.value_objects.insumos_settings import settings_to_raw


@dataclass(frozen=True)
class SaveInsumosConfigPorts:
    settings: InsumosSettingsRepository


class SaveInsumosConfig:
    def __init__(self, ports: SaveInsumosConfigPorts) -> None:
        self._ports = ports

    async def execute(self, command: SaveConfigCommand) -> SaveConfigResult:
        emails = [email.strip() for email in command.logistics_mail_to if email.strip()]
        ops_emails = [email.strip() for email in command.ops_alert_mail_to if email.strip()]
        error = validate_settings(command.settings, emails, ops_emails)
        if error is not None:
            return SaveConfigResult(ok=False, error=error)
        settings = replace(
            command.settings,
            logistics_mail_to=",".join(emails),
            ops_alert_mail_to=",".join(ops_emails),
        )
        await self._ports.settings.set_all(settings_to_raw(settings))
        return SaveConfigResult(ok=True)
