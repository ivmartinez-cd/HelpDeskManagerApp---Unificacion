"""Caso de uso GetDashboard — port de compute_dashboard_state (pending_requests.py).

Las 4 fases del legacy, en async:
1. Por cliente habilitado: solicitudes OUTSTANDING (sin stale) + ids procesados + series
   de los equipos — errores por cliente aislados (el dashboard nunca cae entero).
2. Un único refresh SOAP global de estados de pedidos procesados (con TTL de cache).
3. Liberar solicitudes cuyo pedido quedó Anulado/Cancelado en CD (audit RELEASED).
4. Agregación pura por cliente (domain/services/dashboard_summary).

Pendiente explícito: el TTLCache de equipos del legacy (device_cache) se porta junto con
el poller — hasta entonces cada carga consulta los equipos en vivo; y pending_list (el
insumo del job de alertas) llega con el port del módulo de alertas.
"""

import asyncio
import logging
from dataclasses import dataclass

from src.modules.insumos.application.dtos.dashboard import DashboardResult, DashboardThresholds
from src.modules.insumos.domain.entities.audit_record import EVENT_RELEASED, AuditRecord
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.repositories.customer_config_repository import (
    CustomerConfigRepository,
)
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.repositories.insumos_settings_repository import (
    InsumosSettingsRepository,
)
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.services.dashboard_summary import (
    CustomerRequests,
    CustomerSummary,
    RequestSnapshot,
    summarize_customers,
)
from src.modules.insumos.domain.services.maintenance_kit import is_maintenance_kit
from src.modules.insumos.domain.services.stale_replacement import is_stale_replaced
from src.modules.insumos.domain.value_objects import cd_state
from src.modules.insumos.domain.value_objects.cd_datetime import parse_cd_datetime
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdSupply
from src.modules.insumos.domain.value_objects.insight_datetime import (
    insight_iso_to_argentina_date,
)
from src.modules.insumos.domain.value_objects.insumos_settings import (
    InsumosSettings,
    settings_from_raw,
)
from src.modules.insumos.domain.value_objects.serial_number import serial_from_supply_fields

logger = logging.getLogger(__name__)

# No re-verificar vía SOAP si el cache fue actualizado hace menos de esto.
_SOAP_TTL_SECONDS = 300


@dataclass(frozen=True)
class GetDashboardPorts:
    insight: InsightGateway
    wsayc: WsAycGateway
    processed: ProcessedRequestRepository
    supply_cache: SupplyCacheRepository
    customers: CustomerConfigRepository
    settings: InsumosSettingsRepository
    audit: OrderAuditRepository


@dataclass(frozen=True)
class _CustomerFetch:
    data: CustomerRequests
    req_to_supply: dict[int, int]
    kits_by_request: dict[int, bool]


class GetDashboard:
    def __init__(self, ports: GetDashboardPorts) -> None:
        self._ports = ports

    async def execute(self, refresh_minutes: int) -> DashboardResult:
        settings = settings_from_raw(await self._ports.settings.get_all())
        customers = await self._ports.customers.list_enabled()
        fetches = list(
            await asyncio.gather(
                *(self._fetch_customer(c.customer_id, c.name) for c in customers)
            )
        )
        released = await self._refresh_and_release(fetches)
        datas = [_without_released(f.data, released) for f in fetches]
        per_customer, totals = await self._summarize(datas, settings)
        return DashboardResult(
            totals=totals,
            loaded_today=await self._ports.processed.count_processed_today(),
            customers_enabled=len(customers),
            per_customer=per_customer,
            thresholds=DashboardThresholds(
                critical=settings.threshold_critical,
                urgent=settings.threshold_urgent,
                warning=settings.threshold_warning,
            ),
            refresh_minutes=refresh_minutes,
        )

    # ------------------------------------------------------ fase 1: por cliente --

    async def _fetch_customer(self, customer_id: int, name: str) -> _CustomerFetch:
        try:
            return await self._fetch_customer_data(customer_id, name)
        except Exception as exc:
            logger.error(
                "Dashboard: no se pudieron consultar las solicitudes del cliente %s",
                customer_id,
                exc_info=exc,
            )
            data = CustomerRequests(
                customer_id=customer_id,
                name=name,
                requests=(),
                processed_ids=frozenset(),
                error="No se pudo consultar este cliente",
            )
            return _CustomerFetch(data=data, req_to_supply={}, kits_by_request={})

    async def _fetch_customer_data(self, customer_id: int, name: str) -> _CustomerFetch:
        raw = await self._ports.insight.get_consumable_requests(
            customer_id, workflow_status="OUTSTANDING"
        )
        fresh = [
            r for r in raw if not is_stale_replaced(r.get("requested"), r.get("replacedDate"))
        ]
        processed = await self._ports.processed.get_processed_ids([r["id"] for r in fresh])
        req_to_supply = await self._ports.processed.get_supply_ids(list(processed))
        snapshots = await self._build_snapshots(fresh)
        data = CustomerRequests(
            customer_id=customer_id,
            name=name,
            requests=tuple(snapshots),
            processed_ids=frozenset(processed),
        )
        kits = {s.hp_request_id: s.is_maintenance_kit for s in snapshots}
        return _CustomerFetch(data=data, req_to_supply=req_to_supply, kits_by_request=kits)

    async def _build_snapshots(self, requests: list[JsonDict]) -> list[RequestSnapshot]:
        device_ids = sorted({int(r["deviceId"]) for r in requests})
        devices = await asyncio.gather(
            *(self._ports.insight.get_device_by_id(did) for did in device_ids)
        )
        serial_by_device = {
            did: str(d.get("serialNumber") or "")
            for did, d in zip(device_ids, devices, strict=True)
        }
        return [_snapshot_from(r, serial_by_device) for r in requests]

    # ------------------------------------- fases 2 y 3: refresh SOAP + liberación --

    async def _refresh_and_release(self, fetches: list[_CustomerFetch]) -> set[int]:
        req_to_supply: dict[int, int] = {}
        kits: dict[int, bool] = {}
        fetch_by_request: dict[int, _CustomerFetch] = {}
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
        statuses = await self._ports.supply_cache.get_statuses_batch(supply_ids)
        today_ids = await self._ports.processed.get_today_processed_ids(list(req_to_supply))
        recent = await self._ports.supply_cache.get_recently_cached_ids(
            supply_ids, _SOAP_TTL_SECONDS
        )
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
            return await self._ports.wsayc.fetch_incident_by_id(supply_id), True
        return await self._ports.wsayc.fetch_supply_by_id(supply_id), False

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
            await self._ports.supply_cache.upsert(cache_updates)

    async def _release(
        self, req_id: int, supply_id: int, estado: str, fetch: _CustomerFetch
    ) -> None:
        logger.info("dashboard: supply %d %s → liberando solicitud %d", supply_id, estado, req_id)
        processed = await self._ports.processed.get(req_id)
        await self._ports.processed.mark_cancelled(req_id)
        snapshot = next((s for s in fetch.data.requests if s.hp_request_id == req_id), None)
        detail = f"supply {supply_id} {estado}"
        await self._ports.audit.record(
            _released_record(req_id, fetch.data, detail, processed, snapshot)
        )

    # -------------------------------------------------------- fase 4: agregación --

    async def _summarize(
        self, datas: list[CustomerRequests], settings: InsumosSettings
    ) -> tuple[list[CustomerSummary], dict[str, int]]:
        pending_serials = sorted(
            {
                s.device_serial
                for data in datas
                for s in data.requests
                if s.hp_request_id not in data.processed_ids and s.device_serial
            }
        )
        supplies = await self._ports.supply_cache.get_noncancelled_by_serials(pending_serials)
        own_orders = await self._ports.processed.get_created_by_serials(pending_serials)
        return summarize_customers(datas, settings, supplies, own_orders)


def _snapshot_from(request: JsonDict, serial_by_device: dict[int, str]) -> RequestSnapshot:
    consumable = request.get("consumable") or {}
    reorder_part = consumable.get("reorderPart") or {}
    device_id = int(request["deviceId"])
    return RequestSnapshot(
        hp_request_id=int(request["id"]),
        device_id=device_id,
        device_serial=serial_by_device.get(device_id, ""),
        sku=str(consumable.get("sku") or ""),
        description=str(consumable.get("description") or ""),
        days_left=consumable.get("daysLeft"),
        requested_day=insight_iso_to_argentina_date(request.get("requested")),
        is_maintenance_kit=is_maintenance_kit(
            str(consumable.get("description") or ""), str(reorder_part.get("type") or "")
        ),
    )


def _without_released(data: CustomerRequests, released: set[int]) -> CustomerRequests:
    """Las solicitudes liberadas en fase 3 vuelven a contar como pendientes."""
    if not released & set(data.processed_ids):
        return data
    return CustomerRequests(
        customer_id=data.customer_id,
        name=data.name,
        requests=data.requests,
        processed_ids=frozenset(data.processed_ids - released),
        error=data.error,
    )


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
