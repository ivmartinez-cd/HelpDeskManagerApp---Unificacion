"""Caso de uso DismissRequest — port de POST /api/requests/{id}/dismiss (actions.py).

Descarta la solicitud directamente en HP SDS (status_update=DELETE, el mismo que usa
el descarte automático de la ventana de validación) y registra DISMISSED en el
Historial. Si la solicitud tenía un pedido vinculado, el registro local se libera
(mark_cancelled) — el pedido en CD no se toca: para eso está /cancel.

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
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DismissRequestPorts:
    insight: InsightGateway
    processed: ProcessedRequestRepository
    audit: OrderAuditRepository


class DismissRequest:
    def __init__(self, ports: DismissRequestPorts) -> None:
        self._ports = ports

    async def execute(self, command: DismissCommand) -> DismissResult:
        try:
            await self._ports.insight.update_consumable_request(
                request_id=command.hp_request_id,
                status_update="DELETE",
                comment="Descartado manualmente desde la app SDS Autoloader",
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
        return DismissResult(ok=True)
