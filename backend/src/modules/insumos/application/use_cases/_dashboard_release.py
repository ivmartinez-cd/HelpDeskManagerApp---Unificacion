"""Fases 2 y 3 de GetDashboard: un único refresh SOAP global de estados de
pedidos procesados (con TTL de cache) y liberación de solicitudes cuyo pedido
quedó Anulado/Cancelado en CD (audit RELEASED). Separado de get_dashboard.py
porque ese archivo ya superaba el tamaño máximo (§4)."""

import asyncio
import logging

from src.modules.insumos.application.use_cases._dashboard_customer_fetch import CustomerFetch
from src.modules.insumos.domain.entities.audit_record import EVENT_RELEASED, AuditRecord
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.services.dashboard_summary import CustomerRequests, RequestSnapshot
from src.modules.insumos.domain.value_objects import cd_state
from src.modules.insumos.domain.value_objects.cd_datetime import parse_cd_datetime
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdSupply
from src.modules.insumos.domain.value_objects.serial_number import serial_from_supply_fields

logger = logging.getLogger(__name__)

# No re-verificar vía SOAP si el cache fue actualizado hace menos de esto.
_SOAP_TTL_SECONDS = 300


class ReleaseReconciler:
    def __init__(
        self,
        wsayc: WsAycGateway,
        processed: ProcessedRequestRepository,
        supply_cache: SupplyCacheRepository,
        audit: OrderAuditRepository,
    ) -> None:
        self._wsayc = wsayc
        self._processed = processed
        self._supply_cache = supply_cache
        self._audit = audit

    async def execute(self, fetches: list[CustomerFetch]) -> set[int]:
        req_to_supply: dict[int, int] = {}
        kits: dict[int, bool] = {}
        fetch_by_request: dict[int, CustomerFetch] = {}
        for fetch in fetches:
            req_to_supply.update(fetch.req_to_supply)
            kits.update(fetch.kits_by_request)
            for rid in fetch.req_to_supply:
                fetch_by_request[rid] = fetch
        if not req_to_supply:
            return set()

        statuses = await self._refresh_statuses(req_to_supply, kits)
        released: set[int] = set()
        for req_id, supply_id in req_to_supply.items():
            estado = statuses.get(supply_id)
            if estado is not None and estado in cd_state.RELEASE_STATES:
                await self._release(req_id, supply_id, estado, fetch_by_request[req_id])
                released.add(req_id)
        return released

    async def _refresh_statuses(
        self, req_to_supply: dict[int, int], kits: dict[int, bool]
    ) -> dict[int, str]:
        supply_ids = list(req_to_supply.values())
        statuses = await self._supply_cache.get_statuses_batch(supply_ids)
        today_ids = await self._processed.get_today_processed_ids(list(req_to_supply))
        recent = await self._supply_cache.get_recently_cached_ids(supply_ids, _SOAP_TTL_SECONDS)
        # Se re-verifica en vivo lo que no está en cache, más los pedidos de HOY cuyo
        # estado cacheado no es terminal y ya venció el TTL (los recién creados cambian
        # rápido de estado; el resto se actualiza con el scan periódico).
        to_check = list(
            dict.fromkeys(
                sid
                for rid, sid in req_to_supply.items()
                if sid not in statuses
                or (
                    rid in today_ids
                    and statuses.get(sid) not in cd_state.RELEASE_STATES
                    and sid not in recent
                )
            )
        )
        if to_check:
            request_by_supply = {sid: rid for rid, sid in req_to_supply.items()}
            results = await asyncio.gather(
                *(
                    self._fetch_live_status(sid, kits.get(request_by_supply[sid], False))
                    for sid in to_check
                )
            )
            await self._apply_live_statuses(statuses, to_check, results)
        return statuses

    async def _fetch_live_status(
        self, supply_id: int, is_kit: bool
    ) -> tuple[CdSupply | None, bool]:
        if is_kit:
            return await self._wsayc.fetch_incident_by_id(supply_id), True
        return await self._wsayc.fetch_supply_by_id(supply_id), False

    async def _apply_live_statuses(
        self,
        statuses: dict[int, str],
        checked_ids: list[int],
        results: list[tuple[CdSupply | None, bool]],
    ) -> None:
        cache_updates = []
        for supply_id, (item, is_incident) in zip(checked_ids, results, strict=True):
            if item is None:
                continue
            statuses[supply_id] = item.estado
            if not is_incident:
                cache_updates.append(
                    CachedSupply(
                        supply_id=supply_id,
                        serial=serial_from_supply_fields(
                            item.nro_serie_solicitud, item.nro_serie
                        ),
                        estado=item.estado,
                        empresa_id=item.empresa_id,
                        fecha=parse_cd_datetime(item.fecha),
                    )
                )
        if cache_updates:
            await self._supply_cache.upsert(cache_updates)

    async def _release(
        self, req_id: int, supply_id: int, estado: str, fetch: CustomerFetch
    ) -> None:
        logger.info("dashboard: supply %d %s → liberando solicitud %d", supply_id, estado, req_id)
        processed = await self._processed.get(req_id)
        await self._processed.mark_cancelled(req_id)
        snapshot = next((s for s in fetch.data.requests if s.hp_request_id == req_id), None)
        detail = f"supply {supply_id} {estado}"
        await self._audit.record(_released_record(req_id, fetch.data, detail, processed, snapshot))


def _released_record(
    req_id: int,
    data: CustomerRequests,
    detail: str,
    processed: ProcessedRequest | None,
    snapshot: RequestSnapshot | None,
) -> AuditRecord:
    return AuditRecord(
        event=EVENT_RELEASED,
        hp_request_id=req_id,
        customer_id=data.customer_id,
        customer_name=data.name,
        device_serial=processed.device_serial if processed else None,
        sku=processed.sku if processed else None,
        internal_order_id=processed.internal_order_id if processed else None,
        detail=detail,
        description=(snapshot.description if snapshot else None)
        or (processed.description if processed else None),
    )
