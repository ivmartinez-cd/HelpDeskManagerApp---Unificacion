"""Casos de uso de alertas de solicitudes sin cargar — port de routers/alerts.py.

El GET escala las vencidas en el momento en vez de esperar el próximo ciclo del job
de fondo: es el endpoint que pollea el frontend, así que la escalada queda precisa al
minuto sin gastar I/O extra (es un solo UPDATE, no hay llamadas externas).

El job periódico de escalado NO está portado: no hace falta para que esto funcione,
solo para que las alertas escalen cuando nadie tiene la pantalla abierta.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, tzinfo

from src.modules.insumos.domain.entities.request_alert import RequestAlert
from src.modules.insumos.domain.repositories.insumos_settings_repository import (
    InsumosSettingsRepository,
)
from src.modules.insumos.domain.repositories.request_alert_repository import (
    RequestAlertRepository,
)
from src.modules.insumos.domain.services.alert_escalation import (
    escalation_cutoff,
    is_escalation_window,
)
from src.modules.insumos.domain.value_objects.insumos_settings import settings_from_raw


@dataclass(frozen=True)
class AlertsPorts:
    alerts: RequestAlertRepository
    settings: InsumosSettingsRepository


class ListAlerts:
    def __init__(self, ports: AlertsPorts, timezone: tzinfo) -> None:
        self._ports = ports
        self._timezone = timezone

    async def execute(self) -> list[RequestAlert]:
        """Escala lo vencido (si estamos dentro del horario en que alguien puede
        atenderlo) y devuelve las alertas activas, la más antigua primero."""
        settings = settings_from_raw(await self._ports.settings.get_all())
        now = datetime.now(UTC)
        if is_escalation_window(now.astimezone(self._timezone), settings):
            await self._ports.alerts.escalate_due(escalation_cutoff(now, settings))
        return await self._ports.alerts.list_escalated()


class AcknowledgeAlerts:
    def __init__(self, ports: AlertsPorts) -> None:
        self._ports = ports

    async def execute(self, hp_request_ids: Sequence[int]) -> int:
        """Reconoce alertas escaladas a mano: el operario ya las está gestionando pero
        todavía no puede cargar el pedido. Se resuelven solas cuando se carga."""
        return await self._ports.alerts.acknowledge(hp_request_ids)
