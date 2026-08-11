"""Caso de uso SyncPendingAlerts — job de sincronización de request_alerts.

Para cada cliente habilitado, trae las solicitudes OUTSTANDING de Insight,
filtra las stale y las ya procesadas, y hace upsert en request_alerts. Las que
ya no están pendientes pasan a RESOLVED. Al final, escala las que superaron el
umbral de tiempo (si estamos dentro del horario laboral configurado).

Se llama desde el job de fondo de alertas cada ~15 minutos; el ListAlerts
(endpoint HTTP) también escala en vivo, así que la escalada desde el job solo
sirve cuando nadie tiene la pantalla abierta.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from src.modules.insumos.domain.entities.request_alert import AlertPendingEntry
from src.modules.insumos.domain.repositories.customer_config_repository import (
    CustomerConfigRepository,
)
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway
from src.modules.insumos.domain.repositories.insumos_settings_repository import (
    InsumosSettingsRepository,
)
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)
from src.modules.insumos.domain.repositories.request_alert_repository import (
    RequestAlertRepository,
)
from src.modules.insumos.domain.services.alert_escalation import (
    escalation_cutoff,
    is_escalation_window,
)
from src.modules.insumos.domain.services.stale_replacement import is_stale_replaced
from src.modules.insumos.domain.value_objects.insight_datetime import parse_insight_utc
from src.modules.insumos.domain.value_objects.insumos_settings import settings_from_raw

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SyncPendingAlertsPorts:
    insight: InsightGateway
    customers: CustomerConfigRepository
    processed: ProcessedRequestRepository
    alerts: RequestAlertRepository
    settings: InsumosSettingsRepository


class SyncPendingAlerts:
    def __init__(self, ports: SyncPendingAlertsPorts, timezone: ZoneInfo) -> None:
        self._ports = ports
        self._timezone = timezone

    async def execute(self) -> int:
        """Sincroniza alertas y devuelve cuántas están pendientes ahora."""
        settings = settings_from_raw(await self._ports.settings.get_all())
        customers = await self._ports.customers.list_enabled()
        pending: list[AlertPendingEntry] = []
        for customer in customers:
            pending.extend(await self._collect(customer.customer_id, customer.name))
        await self._ports.alerts.sync_pending(pending)
        now = datetime.now(UTC)
        if is_escalation_window(now.astimezone(self._timezone), settings):
            await self._ports.alerts.escalate_due(escalation_cutoff(now, settings))
        return len(pending)

    async def _collect(self, customer_id: int, customer_name: str) -> list[AlertPendingEntry]:
        try:
            requests = await self._ports.insight.get_consumable_requests(
                customer_id, workflow_status="OUTSTANDING"
            )
        except Exception as exc:
            logger.error(
                "sync_pending_alerts: Insight falló para cliente %s",
                customer_id,
                extra={"customer_id": customer_id},
                exc_info=exc,
            )
            return []
        request_ids = [int(req["id"]) for req in requests]
        if not request_ids:
            return []
        processed = await self._ports.processed.get_processed_ids(request_ids)
        return [
            AlertPendingEntry(
                hp_request_id=int(req["id"]),
                customer_id=customer_id,
                customer_name=customer_name,
                device_serial="",
                sku=str((req.get("consumable") or {}).get("sku") or ""),
                description=str((req.get("consumable") or {}).get("description") or ""),
                requested_at=parse_insight_utc(req.get("requested")),
            )
            for req in requests
            if not is_stale_replaced(
                req.get("requested"),
                (req.get("consumable") or {}).get("replacedDate"),
            )
            and int(req["id"]) not in processed
        ]
