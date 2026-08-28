"""Caso de uso IgnoreRequest — port de POST /api/requests/{id}/ignore.

Ignora PERMANENTEMENTE en HP SDS una solicitud que sigue reemitiéndose sin que
corresponda cargar nada — típicamente porque el pedido asociado (badge de "pedido
despachado sin confirmar entrega") ya se dio por resuelto, pero también sirve para una
solicitud recurrente sin pedido asociado (ej. un consumible que oscila siempre en el
mismo nivel y no amerita pedirse).

A diferencia de DismissRequest (IGNORE temporal cuando hay pedido asociado, con
hp_request_id guardado para que el job de fondo mande UNIGNORE cuando el pedido
resuelva), acá se registra con hp_request_id=None: nunca entra al chequeo de
UNIGNORE, así que el descarte no se revierte solo. Si no hay pedido asociado, no hay
nada que suprimir localmente por supply_id — el propio IGNORE en HP SDS ya evita que
la alerta vuelva a aparecer.
"""

import logging
from dataclasses import dataclass

from src.modules.insumos.application.dtos.request_actions import IgnoreCommand, IgnoreResult
from src.modules.insumos.domain.entities.audit_record import EVENT_IGNORED, AuditRecord
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
class IgnoreRequestPorts:
    insight: InsightGateway
    processed: ProcessedRequestRepository
    audit: OrderAuditRepository
    dismissed: DismissedSupplyRepository


class IgnoreRequest:
    def __init__(self, ports: IgnoreRequestPorts) -> None:
        self._ports = ports

    async def execute(self, command: IgnoreCommand) -> IgnoreResult:
        has_supply = command.supply_id is not None and not command.supply_id.startswith(
            _DRYRUN_PREFIX
        )
        supply_num_id = _parse_supply_id(command.supply_id) if has_supply else None
        if has_supply and supply_num_id is None:
            return IgnoreResult(ok=False, error="No se pudo interpretar el número de pedido.")
        error = await self._call_insight(command, has_supply)
        if error is not None:
            return IgnoreResult(ok=False, error=error)
        await self._persist_local(command, has_supply, supply_num_id)
        return IgnoreResult(ok=True)

    async def _call_insight(self, command: IgnoreCommand, has_supply: bool) -> str | None:
        try:
            await self._ports.insight.update_consumable_request(
                request_id=command.hp_request_id,
                status_update="IGNORE",
                comment=_comment(command, has_supply),
            )
        except Exception as exc:
            logger.error(
                "No se pudo ignorar la solicitud %s en HP SDS", command.hp_request_id, exc_info=exc
            )
            return "No se pudo ignorar la solicitud en HP SDS. Intentá de nuevo."
        return None

    async def _persist_local(
        self, command: IgnoreCommand, has_supply: bool, supply_num_id: int | None
    ) -> None:
        await self._ports.audit.record(_audit_record(command, has_supply))
        existing = await self._ports.processed.get(command.hp_request_id)
        if existing is not None and existing.status != STATUS_CANCELLED:
            await self._ports.processed.mark_cancelled(command.hp_request_id)
        if supply_num_id is not None:
            await self._ports.dismissed.mark_dismissed(
                supply_num_id, command.device_serial, hp_request_id=None
            )


def _audit_record(command: IgnoreCommand, has_supply: bool) -> AuditRecord:
    return AuditRecord(
        event=EVENT_IGNORED,
        hp_request_id=command.hp_request_id,
        customer_id=command.customer_id,
        customer_name=command.customer_name or None,
        device_serial=command.device_serial,
        sku=command.sku,
        detail=_audit_detail(command, has_supply),
    )


def _parse_supply_id(supply_id: str | None) -> int | None:
    assert supply_id is not None
    try:
        return int(supply_id.split("-")[0])
    except (ValueError, IndexError):
        return None


def _comment(command: IgnoreCommand, has_supply: bool) -> str:
    if has_supply:
        estado = f" ({command.supply_status})" if command.supply_status else ""
        return (
            "Ignorada permanentemente desde la app SDS Autoloader — pedido "
            f"{command.supply_id}{estado} ya cargado en Canal Directo"
        )
    return (
        "Ignorada permanentemente desde la app SDS Autoloader — sin pedido asociado "
        "en Canal Directo"
    )


def _audit_detail(command: IgnoreCommand, has_supply: bool) -> str:
    if has_supply:
        return (
            f"Solicitud ignorada permanentemente en HP SDS (pedido {command.supply_id} "
            "ya cargado)"
        )
    return "Solicitud ignorada permanentemente en HP SDS (sin pedido asociado)"
