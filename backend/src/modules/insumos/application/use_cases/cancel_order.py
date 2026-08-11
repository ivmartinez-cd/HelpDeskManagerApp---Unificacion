"""Caso de uso CancelOrder — port de POST /api/requests/{id}/cancel (actions.py).

Anula en Canal Directo el pedido (o incidente de ST) asociado a la solicitud y libera
el registro local. Como voidSupply/voidIncident responden "true" incondicionalmente,
la anulación solo se da por buena si la relectura confirma Anulado/Cancelado.

A diferencia del legacy (que borraba la fila de processed_requests), acá "liberar" es
mark_cancelled: la fila queda como rastro pero la autocarga no la repite y /load
permite recargar (ver processed_request.py).
"""

import logging
from dataclasses import dataclass

from src.modules.insumos.application.dtos.request_actions import CancelResult
from src.modules.insumos.domain.entities.audit_record import EVENT_CANCELLED, AuditRecord
from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CANCELLED,
    ProcessedRequest,
)
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.value_objects import cd_state
from src.modules.insumos.domain.value_objects.cd_datetime import parse_cd_datetime
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdSupply
from src.modules.insumos.domain.value_objects.serial_number import serial_from_supply_fields

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CancelOrderPorts:
    wsayc: WsAycGateway
    processed: ProcessedRequestRepository
    supply_cache: SupplyCacheRepository
    audit: OrderAuditRepository


class CancelOrder:
    def __init__(self, ports: CancelOrderPorts) -> None:
        self._ports = ports

    async def execute(self, hp_request_id: int) -> CancelResult:
        processed = await self._ports.processed.get(hp_request_id)
        if processed is None or processed.status == STATUS_CANCELLED:
            return CancelResult(ok=False, error="No hay un pedido cargado para esta solicitud.")
        order_id = processed.internal_order_id
        try:
            supply_id = int(order_id.split("-")[0])
        except (ValueError, IndexError):
            # Cubre también los DRYRUN-: un pedido simulado no existe en CD, no hay
            # nada que anular allá (mismo comportamiento que el legacy).
            logger.error("cancel_order: internal_order_id con formato inesperado: %s", order_id)
            return CancelResult(
                ok=False, error="No se pudo interpretar el número de pedido o incidente."
            )
        return await self._void_and_confirm(hp_request_id, processed, supply_id)

    async def _void_and_confirm(
        self, hp_request_id: int, processed: ProcessedRequest, supply_id: int
    ) -> CancelResult:
        is_incident = await self._is_incident(supply_id)
        kind = "incidente" if is_incident else "pedido"
        voided = await (
            self._ports.wsayc.void_incident(supply_id)
            if is_incident
            else self._ports.wsayc.void_supply(supply_id)
        )
        if not voided:
            return CancelResult(
                ok=False,
                error=f"No se pudo anular el {kind} en Canal Directo. Intentá de nuevo.",
            )
        # Reconsultar para confirmar: void* responde "true" incondicionalmente.
        item = await (
            self._ports.wsayc.fetch_incident_by_id(supply_id)
            if is_incident
            else self._ports.wsayc.fetch_supply_by_id(supply_id)
        )
        estado = item.estado if item else None
        if item is None or estado not in cd_state.RELEASE_STATES:
            logger.error(
                "cancel_order: void %s (%d) no confirmó la anulación (estado actual: %s)",
                kind,
                supply_id,
                estado,
            )
            return CancelResult(
                ok=False,
                error=f"Canal Directo no confirmó la anulación (estado actual: "
                f"{estado or 'desconocido'}). Verificá manualmente en el portal.",
            )
        await self._release(hp_request_id, processed, supply_id, item, is_incident)
        return CancelResult(ok=True, supply_status=estado)

    async def _is_incident(self, supply_id: int) -> bool:
        """El ID puede ser de un supply o de un incidente de ST (kit de mantenimiento)
        — se determina consultando el SOAP, igual que el legacy."""
        incident = await self._ports.wsayc.fetch_incident_by_id(supply_id)
        return incident is not None and incident.supply_id == supply_id

    async def _release(
        self,
        hp_request_id: int,
        processed: ProcessedRequest,
        supply_id: int,
        item: CdSupply,
        is_incident: bool,
    ) -> None:
        if not is_incident:
            # Reflejar el estado nuevo en el cache al instante — sin esto el bloqueo 2
            # de /load seguiría viendo el pedido como activo hasta el próximo scan.
            await self._ports.supply_cache.upsert(
                [
                    CachedSupply(
                        supply_id=supply_id,
                        serial=serial_from_supply_fields(item.nro_serie_solicitud, item.nro_serie),
                        estado=item.estado,
                        empresa_id=item.empresa_id,
                        fecha=parse_cd_datetime(item.fecha),
                    )
                ]
            )
        await self._ports.processed.mark_cancelled(hp_request_id)
        kind = "incidente" if is_incident else "supply"
        await self._ports.audit.record(
            AuditRecord(
                event=EVENT_CANCELLED,
                hp_request_id=hp_request_id,
                customer_id=processed.customer_id,
                device_serial=processed.device_serial,
                sku=processed.sku,
                internal_order_id=processed.internal_order_id,
                detail=f"Anulado manualmente desde la app ({kind} {supply_id})",
                description=processed.description,
            )
        )
