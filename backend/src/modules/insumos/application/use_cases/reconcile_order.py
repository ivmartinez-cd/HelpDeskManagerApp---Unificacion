"""Caso de uso ReconcileOrder — port de POST /api/requests/{id}/reconcile (actions.py).

Vincula manualmente un pedido que ya existe de verdad en Canal Directo pero que la app
no registró como propio — el caso típico es un evento FAILED cuya verificación
post-creación falló por lag de lectura de CD, aunque persistNewSupply sí lo haya
creado. NUNCA crea un pedido nuevo: solo busca por referencia exacta (SDS-{id}) uno
que ya exista y, si lo encuentra, lo vincula.

Igual que /load: la solicitud se re-deriva contra Insight (nunca se confía en el
body para serie/sku) y todo corre dentro del claim serie+sku.

Pendiente de pasos posteriores (explícito, no olvidado): resolver la alerta activa
(request_alerts) al vincular — llega con el port del módulo de alertas.
"""

import logging
from dataclasses import dataclass

from src.modules.insumos.application.dtos.request_actions import ReconcileCommand, ReconcileResult
from src.modules.insumos.domain.entities.audit_record import EVENT_CREATED, AuditRecord
from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CANCELLED,
    ProcessedRequest,
)
from src.modules.insumos.domain.errors import OrderAlreadyInProgressError
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)
from src.modules.insumos.domain.services.claimed_order_creation import ClaimedOrderCreation
from src.modules.insumos.domain.services.supply_lookup import CanalDirectoSupplyLookup
from src.modules.insumos.domain.value_objects.insight_datetime import parse_insight_utc
from src.modules.insumos.domain.value_objects.order_reference import order_reference
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.modules.insumos.domain.value_objects.supply_id import supply_id_full

logger = logging.getLogger(__name__)

_DRYRUN_PREFIX = "DRYRUN-"

_NOT_FOUND_ERROR = (
    "No se encontró ningún pedido en Canal Directo con esta referencia. Puede que "
    "todavía no esté indexado (probá de nuevo en unos minutos) o que realmente no se "
    "haya creado — en ese caso, reintentá la carga normal."
)


@dataclass(frozen=True)
class ReconcileOrderPorts:
    insight: InsightGateway
    processed: ProcessedRequestRepository
    audit: OrderAuditRepository
    supply_lookup: CanalDirectoSupplyLookup
    claimed_creation: ClaimedOrderCreation


@dataclass(frozen=True)
class ReconcileOrderConfig:
    order_settings: CanalDirectoOrderSettings
    insight_mark_actioned: bool
    insight_status_on_order: str


@dataclass(frozen=True)
class _Resolved:
    device_id: int
    device_serial: str
    consumable: JsonDict
    requested: str | None


class ReconcileOrder:
    def __init__(self, ports: ReconcileOrderPorts, config: ReconcileOrderConfig) -> None:
        self._ports = ports
        self._config = config

    async def execute(self, command: ReconcileCommand) -> ReconcileResult:
        resolved = await self._resolve(command)
        if isinstance(resolved, ReconcileResult):
            return resolved

        async def link() -> ReconcileResult:
            return await self._link(command, resolved)

        try:
            return await self._ports.claimed_creation.run(
                device_serial=resolved.device_serial,
                sku=str(resolved.consumable.get("sku") or ""),
                action=link,
            )
        except OrderAlreadyInProgressError as exc:
            return ReconcileResult(ok=False, error=str(exc))

    async def _resolve(self, command: ReconcileCommand) -> _Resolved | ReconcileResult:
        """Mismo criterio que /load: nunca confiar en el body para serie/sku."""
        try:
            requests = await self._ports.insight.get_consumable_requests(
                command.customer_id, workflow_status="OUTSTANDING"
            )
        except Exception as exc:
            logger.error(
                "No se pudo verificar la solicitud %s contra Insight",
                command.hp_request_id,
                exc_info=exc,
            )
            return ReconcileResult(
                ok=False,
                error="No se pudo verificar la solicitud contra Insight. Intentá de nuevo.",
            )
        matched = next((r for r in requests if r.get("id") == command.hp_request_id), None)
        if matched is None:
            return ReconcileResult(
                ok=False,
                error="La solicitud ya no está pendiente en Insight para este cliente — "
                "si el pedido se creó igual, revisalo manualmente en Canal Directo.",
            )
        device_id = int(matched["deviceId"])
        device = await self._ports.insight.get_device_by_id(device_id)
        device_serial = str(device.get("serialNumber") or "")
        if not device_serial:
            return ReconcileResult(
                ok=False,
                error="No se pudo determinar el número de serie del equipo desde Insight.",
            )
        return _Resolved(
            device_id=device_id,
            device_serial=device_serial,
            consumable=matched.get("consumable") or {},
            requested=matched.get("requested"),
        )

    async def _link(self, command: ReconcileCommand, resolved: _Resolved) -> ReconcileResult:
        existing = await self._ports.processed.get(command.hp_request_id)
        if existing is not None and existing.status != STATUS_CANCELLED:
            order_id = existing.internal_order_id
            return ReconcileResult(
                ok=True,
                order_id=order_id,
                supply_url=self._supply_url_for(order_id),
                already_linked=True,
            )
        supply = await self._ports.supply_lookup.find_order_by_reference(
            resolved.device_serial, order_reference(command.hp_request_id)
        )
        if supply is None:
            return ReconcileResult(ok=False, error=_NOT_FOUND_ERROR)
        order_id = supply_id_full(supply.supply_id)
        await self._record_link(command, resolved, order_id)
        await self._mark_insight_actioned(command.hp_request_id, order_id)
        return ReconcileResult(
            ok=True,
            order_id=order_id,
            supply_url=self._config.order_settings.supply_web_url(supply.supply_id),
        )

    async def _record_link(
        self, command: ReconcileCommand, resolved: _Resolved, order_id: str
    ) -> None:
        consumable = resolved.consumable
        percent_left = consumable.get("percentLeft")
        initial_percent = round(percent_left) if percent_left is not None else None
        await self._ports.processed.mark_processed(
            ProcessedRequest(
                hp_request_id=command.hp_request_id,
                device_id=resolved.device_id,
                device_serial=resolved.device_serial,
                customer_id=command.customer_id,
                sku=str(consumable.get("sku") or ""),
                internal_order_id=order_id,
                description=str(consumable.get("description") or ""),
                initial_percent_left=initial_percent,
                initial_days_left=consumable.get("daysLeft"),
                initial_pages_left=consumable.get("pagesLeft"),
            )
        )
        await self._ports.audit.record(
            AuditRecord(
                event=EVENT_CREATED,
                hp_request_id=command.hp_request_id,
                customer_id=command.customer_id,
                customer_name=command.customer_name or None,
                device_serial=resolved.device_serial,
                sku=str(consumable.get("sku") or ""),
                internal_order_id=order_id,
                detail="Vinculado manualmente desde Historial — la verificación automática "
                "había fallado.",
                hp_request_time=parse_insight_utc(resolved.requested),
                description=str(consumable.get("description") or ""),
                device_id=resolved.device_id,
                initial_percent_left=initial_percent,
                initial_days_left=consumable.get("daysLeft"),
                initial_pages_left=consumable.get("pagesLeft"),
            )
        )

    async def _mark_insight_actioned(self, hp_request_id: int, order_id: str) -> None:
        if not self._config.insight_mark_actioned:
            return
        try:
            await self._ports.insight.update_consumable_request(
                request_id=hp_request_id,
                external_ref=f"CD-{order_id}",
                status_update=self._config.insight_status_on_order,
                comment=f"Pedido vinculado manualmente en Canal Directo: {order_id}",
            )
            logger.info(
                "Insight request %s marcada como %s (ref CD-%s, vinculación manual)",
                hp_request_id,
                self._config.insight_status_on_order,
                order_id,
            )
        except Exception as exc:
            logger.error(
                "No se pudo actualizar Insight para request %s (pedido %s ya vinculado)",
                hp_request_id,
                order_id,
                exc_info=exc,
            )

    def _supply_url_for(self, order_id: str) -> str | None:
        if not order_id or order_id.startswith(_DRYRUN_PREFIX):
            return None
        return f"{self._config.order_settings.portal_base_url}/supplies/view/{order_id}"
