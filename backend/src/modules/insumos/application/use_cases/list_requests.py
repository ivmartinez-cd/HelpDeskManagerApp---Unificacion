"""Caso de uso ListRequests — port de GET /api/requests (routers/requests/query.py),
el endpoint más complejo del legacy: solicitudes OUTSTANDING enriquecidas con datos del
equipo, severidad, ventana de validación y el pedido asociado en Canal Directo.

Pendiente explícito (llega con el módulo de validación/poller):
- resolve_pending_validations al abrir la pantalla (hoy solo se LEEN las PENDING).
- start_pending_validation para solicitudes elegibles que llegan en 0%.
"""

import asyncio
import logging
from dataclasses import dataclass

from src.modules.insumos.application.dtos.request_rows import RequestRow
from src.modules.insumos.application.use_cases._request_association import (
    AssociationContext,
    RequestAssociation,
)
from src.modules.insumos.application.use_cases.get_dashboard import GetDashboardPorts
from src.modules.insumos.domain.repositories.insight_gateway import JsonDict
from src.modules.insumos.domain.repositories.request_validation_repository import (
    RequestValidationRepository,
)
from src.modules.insumos.domain.services.maintenance_kit import is_maintenance_kit
from src.modules.insumos.domain.services.request_status import status_for_days_left
from src.modules.insumos.domain.services.stale_replacement import is_stale_replaced
from src.modules.insumos.domain.services.supply_lookup import CanalDirectoSupplyLookup
from src.modules.insumos.domain.value_objects.insight_datetime import (
    days_since_contact,
    format_arg_datetime,
    insight_iso_to_argentina_date,
)
from src.modules.insumos.domain.value_objects.insumos_settings import (
    InsumosSettings,
    settings_from_raw,
)
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ListRequestsPorts:
    """Reusa los puertos del dashboard + validaciones y el lookup del portal."""

    dashboard: GetDashboardPorts
    validations: RequestValidationRepository
    supply_lookup: CanalDirectoSupplyLookup


@dataclass(frozen=True)
class ListRequestsConfig:
    order_settings: CanalDirectoOrderSettings
    insight_base_url: str


class ListRequests:
    def __init__(self, ports: ListRequestsPorts, config: ListRequestsConfig) -> None:
        self._ports = ports
        self._config = config

    async def execute(self, customer_id: int | None) -> list[RequestRow]:
        """Todas las filas ya asociadas y ordenadas por daysLeft — presentation pagina."""
        settings = settings_from_raw(await self._ports.dashboard.settings.get_all())
        requests = await self._fetch_requests(customer_id)
        rows = await self._build_rows(requests, settings)
        await self._attach_validations(rows)
        association = RequestAssociation(
            AssociationContext(
                dashboard=self._ports.dashboard,
                supply_lookup=self._ports.supply_lookup,
                order_settings=self._config.order_settings,
            )
        )
        await association.associate(rows)
        rows.sort(key=lambda r: r.days_left)
        return rows

    async def _fetch_requests(self, customer_id: int | None) -> list[JsonDict]:
        if customer_id is not None:
            customers = {
                c.customer_id: c.name for c in await self._ports.dashboard.customers.list_enabled()
            }
            raw = await self._ports.dashboard.insight.get_consumable_requests(
                customer_id, workflow_status="OUTSTANDING"
            )
            return _tag_customer(_fresh(raw), customer_id, customers.get(customer_id, ""))
        enabled = await self._ports.dashboard.customers.list_enabled()
        per_customer = await asyncio.gather(
            *(self._fetch_for_customer(c.customer_id, c.name) for c in enabled)
        )
        return [request for batch in per_customer for request in batch]

    async def _fetch_for_customer(self, customer_id: int, name: str) -> list[JsonDict]:
        try:
            raw = await self._ports.dashboard.insight.get_consumable_requests(
                customer_id, workflow_status="OUTSTANDING"
            )
            return _tag_customer(_fresh(raw), customer_id, name)
        except Exception as exc:
            logger.error(
                "list_requests: fallo consultando al cliente %s", customer_id, exc_info=exc
            )
            return []

    async def _build_rows(
        self, requests: list[JsonDict], settings: InsumosSettings
    ) -> list[RequestRow]:
        device_ids = sorted({int(r["deviceId"]) for r in requests})
        devices = await asyncio.gather(
            *(self._ports.dashboard.insight.get_device_by_id(did) for did in device_ids)
        )
        devices_by_id = dict(zip(device_ids, devices, strict=True))
        processed_orders = await self._ports.dashboard.processed.get_processed_ids(
            [r["id"] for r in requests]
        )
        internal_ids = {
            row.hp_request_id: row.internal_order_id
            for rid in processed_orders
            if (row := await self._ports.dashboard.processed.get(rid)) is not None
        }
        return [
            self._row_from(r, devices_by_id.get(int(r["deviceId"]), {}), internal_ids, settings)
            for r in requests
        ]

    def _row_from(
        self,
        request: JsonDict,
        device: JsonDict,
        internal_ids: dict[int, str],
        settings: InsumosSettings,
    ) -> RequestRow:
        consumable = request.get("consumable") or {}
        reorder_part = consumable.get("reorderPart") or {}
        days_left = int(consumable.get("daysLeft") or 0)
        status_key, status_label = status_for_days_left(days_left, settings)
        last_contact = device.get("lastContact")
        days_offline = days_since_contact(last_contact)
        return RequestRow(
            request_id=int(request["id"]),
            device_id=int(request["deviceId"]),
            customer_id=request.get("customerId"),
            customer_name=request.get("customerName"),
            store=str((device.get("extendedFields") or {}).get("zone") or ""),
            serial=str(device.get("serialNumber") or ""),
            description=str(consumable.get("description") or ""),
            sku=str(consumable.get("sku") or ""),
            percent_left=consumable.get("percentLeft"),
            days_left=days_left,
            pages_left=consumable.get("pagesLeft"),
            consumable_index=consumable.get("index"),
            consumable_url=_device_portal_url(
                self._config.insight_base_url, int(request["deviceId"])
            ),
            time=_safe_local_time(request.get("requested")),
            raw_time=request.get("requested"),
            status_key=status_key,
            status_label=status_label,
            order_id=internal_ids.get(int(request["id"])),
            requested_percent=request.get("requestedLevel"),
            requested_days_left=request.get("requestedDaysLeft"),
            last_contact=last_contact,
            days_offline=days_offline,
            is_stale_offline=days_offline is not None
            and days_offline > settings.stale_device_days,
            requested_day=insight_iso_to_argentina_date(request.get("requested")),
            is_maintenance_kit=is_maintenance_kit(
                str(consumable.get("description") or ""), str(reorder_part.get("type") or "")
            ),
        )

    async def _attach_validations(self, rows: list[RequestRow]) -> None:
        pending = await self._ports.validations.get_pending_batch([r.request_id for r in rows])
        for row in rows:
            validation = pending.get(row.request_id)
            if validation is None:
                continue
            row.validation_pending = True
            row.validation_deadline = validation.deadline_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            row.validation_swap_note = validation.swap_note
            row.validation_diagnosis_headline = validation.diagnosis_headline
            row.validation_diagnosis_detail = validation.diagnosis_detail


def _fresh(requests: list[JsonDict]) -> list[JsonDict]:
    return [
        r for r in requests if not is_stale_replaced(r.get("requested"), r.get("replacedDate"))
    ]


def _tag_customer(requests: list[JsonDict], customer_id: int, name: str) -> list[JsonDict]:
    for request in requests:
        request["customerId"] = customer_id
        request["customerName"] = name
    return requests


def _safe_local_time(iso_utc: object) -> str:
    if not iso_utc:
        return ""
    try:
        return format_arg_datetime(str(iso_utc))
    except ValueError:
        return ""


def _device_portal_url(insight_base_url: str, device_id: int) -> str:
    """Ficha del equipo en el PortalWeb (hermano de PortalAPI en el mismo host) — el
    deep-link al consumible puntual no funciona fuera del JS del portal (legacy)."""
    base = insight_base_url.rstrip("/").removesuffix("/PortalAPI") + "/PortalWeb"
    return f"{base}/devices/{device_id}"
