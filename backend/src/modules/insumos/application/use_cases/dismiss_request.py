"""Caso de uso DismissRequest — port de POST /api/requests/{id}/dismiss (actions.py).

Si la fila tenía un pedido despachado en Canal Directo sin confirmar entrega (badge en
la UI, `supply_id` presente), el descarte usa IGNORE en vez de DELETE: HP SDS deja de
reemitir la alerta mientras dure (a diferencia de DELETE, que solo saca esa alerta
puntual — HP SDS puede reemitirla con otro ID si la condición persiste), y se registra
en dismissed_supplies con el hp_request_id que se marcó IGNORE para que el job de fondo
mande UNIGNORE cuando el pedido resuelva (ver application/jobs/dismiss_reconciliation.py).
Sin pedido asociado, sigue siendo DELETE, igual que antes.

A diferencia del legacy (500 con el detalle técnico de la excepción), acá el error de
negocio viaja como ok=false con mensaje genérico y el detalle queda en el log del
server (mismo criterio que /load — hallazgo #8 del legacy: el detalle técnico no va
a respuestas visibles para cualquier operador).
"""

import logging
from dataclasses import dataclass

from src.modules.insumos.application.dtos.request_actions import DismissCommand, DismissResult
from src.modules.insumos.domain.entities.audit_record import EVENT_DISMISSED, AuditRecord
from src.modules.insumos.domain.entities.processed_request import STATUS_CANCELLED
from src.modules.insumos.domain.repositories.dismissed_supply_repository import (
    DismissedSupplyRepository,
)
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)

logger = logging.getLogger(__name__)

_DRYRUN_PREFIX = "DRYRUN-"


@dataclass(frozen=True)
class DismissRequestPorts:
    insight: InsightGateway
    processed: ProcessedRequestRepository
    audit: OrderAuditRepository
    dismissed: DismissedSupplyRepository


class DismissRequest:
    def __init__(self, ports: DismissRequestPorts) -> None:
        self._ports = ports

    async def execute(self, command: DismissCommand) -> DismissResult:
        has_pending_supply = command.supply_id is not None and not command.supply_id.startswith(
            _DRYRUN_PREFIX
        )
        try:
            await self._ports.insight.update_consumable_request(
                request_id=command.hp_request_id,
                status_update="IGNORE" if has_pending_supply else "DELETE",
                comment=_comment(command, has_pending_supply),
            )
        except Exception as exc:
            logger.error(
                "No se pudo descartar la solicitud %s en HP SDS",
                command.hp_request_id,
                exc_info=exc,
            )
            return DismissResult(
                ok=False,
                error="No se pudo descartar la solicitud en HP SDS. Intentá de nuevo.",
            )
        await self._ports.audit.record(
            AuditRecord(
                event=EVENT_DISMISSED,
                hp_request_id=command.hp_request_id,
                customer_id=command.customer_id,
                customer_name=command.customer_name or None,
                device_serial=command.device_serial,
                sku=command.sku,
                detail="Solicitud descartada manualmente en HP SDS",
            )
        )
        # Liberar el registro local si existiese — la solicitud ya no existe en
        # Insight, no debe quedar contando como "cargada".
        existing = await self._ports.processed.get(command.hp_request_id)
        if existing is not None and existing.status != STATUS_CANCELLED:
            await self._ports.processed.mark_cancelled(command.hp_request_id)
        if has_pending_supply:
            await self._mark_dismissed_supply(command)
        return DismissResult(ok=True)

    async def _mark_dismissed_supply(self, command: DismissCommand) -> None:
        assert command.supply_id is not None
        try:
            supply_num_id = int(command.supply_id.split("-")[0])
        except (ValueError, IndexError):
            logger.warning(
                "dismiss_request: supplyId con formato inesperado: %s", command.supply_id
            )
            return
        await self._ports.dismissed.mark_dismissed(
            supply_num_id, command.device_serial, hp_request_id=command.hp_request_id
        )


def _comment(command: DismissCommand, has_pending_supply: bool) -> str:
    comment = "Descartado manualmente desde la app SDS Autoloader"
    if has_pending_supply:
        estado = f" ({command.supply_status})" if command.supply_status else ""
        comment += (
            f" — ya existe un pedido {command.supply_id}{estado} en Canal Directo "
            "sin confirmar entrega"
        )
    return comment
