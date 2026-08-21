"""Fase 1 de GetDashboard: solicitudes OUTSTANDING (sin stale) de un cliente
habilitado + ids procesados + series de los equipos — errores por cliente
aislados (el dashboard nunca cae entero). Separado de get_dashboard.py porque
ese archivo ya superaba el tamaño máximo (§4)."""

import asyncio
import logging
from dataclasses import dataclass

from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)
from src.modules.insumos.domain.services.dashboard_summary import CustomerRequests, RequestSnapshot
from src.modules.insumos.domain.services.maintenance_kit import is_maintenance_kit
from src.modules.insumos.domain.services.stale_replacement import is_stale_replaced
from src.modules.insumos.domain.value_objects.insight_datetime import (
    insight_iso_to_argentina_date,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CustomerFetch:
    data: CustomerRequests
    req_to_supply: dict[int, int]
    kits_by_request: dict[int, bool]


async def fetch_customer(
    insight: InsightGateway,
    processed: ProcessedRequestRepository,
    customer_id: int,
    name: str,
) -> CustomerFetch:
    try:
        return await _fetch_customer_data(insight, processed, customer_id, name)
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
        return CustomerFetch(data=data, req_to_supply={}, kits_by_request={})


async def _fetch_customer_data(
    insight: InsightGateway,
    processed: ProcessedRequestRepository,
    customer_id: int,
    name: str,
) -> CustomerFetch:
    raw = await insight.get_consumable_requests(customer_id, workflow_status="OUTSTANDING")
    fresh = [r for r in raw if not is_stale_replaced(r.get("requested"), r.get("replacedDate"))]
    processed_ids = await processed.get_processed_ids([r["id"] for r in fresh])
    req_to_supply = await processed.get_supply_ids(list(processed_ids))
    snapshots = await _build_snapshots(insight, fresh)
    data = CustomerRequests(
        customer_id=customer_id,
        name=name,
        requests=tuple(snapshots),
        processed_ids=frozenset(processed_ids),
    )
    kits = {s.hp_request_id: s.is_maintenance_kit for s in snapshots}
    return CustomerFetch(data=data, req_to_supply=req_to_supply, kits_by_request=kits)


async def _build_snapshots(
    insight: InsightGateway, requests: list[JsonDict]
) -> list[RequestSnapshot]:
    device_ids = sorted({int(r["deviceId"]) for r in requests})
    devices = await asyncio.gather(*(insight.get_device_by_id(did) for did in device_ids))
    serial_by_device = {
        did: str(d.get("serialNumber") or "") for did, d in zip(device_ids, devices, strict=True)
    }
    return [_snapshot_from(r, serial_by_device) for r in requests]


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
