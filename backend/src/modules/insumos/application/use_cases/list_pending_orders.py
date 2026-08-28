"""Caso de uso ListPendingOrders — port de compute_pending_orders (pending_orders.py):
pedidos cargados por esta app (processed_requests, CREATED) que siguen circulando en
Canal Directo, para seguir día a día cómo evoluciona el consumo y el ciclo
Pendiente→Remito Generado→Despachado→Entregado hasta que se despachen.

Deliberadamente independiente de /requests: no tiene nada que ver con las alertas
OUTSTANDING/ACTIONED de Insight (esas se resuelven o desaparecen de Insight por su
cuenta antes de que el pedido físico llegue — mezclar ambos conceptos fue el bug de la
primera versión en el legacy). Acá solo importan nuestros pedidos y su estado real en CD.

La construcción de cada fila (enriquecimiento con Insight, backfill de la foto
inicial) vive en `_pending_order_rows.py` — separado porque juntos superaban el
tamaño máximo de archivo (§4).
"""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.modules.insumos.application.dtos.pending_orders import PendingOrderRow
from src.modules.insumos.application.use_cases._pending_order_rows import PendingOrderRowBuilder
from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
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
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.value_objects.cd_datetime import parse_cd_datetime
from src.modules.insumos.domain.value_objects.cd_state import ENTREGADO, is_in_transit
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, SupplyStatusEvent
from src.modules.insumos.domain.value_objects.insumos_settings import settings_from_raw
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.shared.infrastructure.cache.ttl_cache import TTLCache

# include_delivered suma los Entregado de los últimos 7 días — sirve para ver el ciclo
# completo antes de que se pierdan de vista (mismo corte que el legacy).
_DELIVERED_WINDOW_DAYS = 7


@dataclass(frozen=True)
class ListPendingOrdersPorts:
    insight: InsightGateway
    wsayc: WsAycGateway
    processed: ProcessedRequestRepository
    supply_cache: SupplyCacheRepository
    customers: CustomerConfigRepository
    settings: InsumosSettingsRepository


class ListPendingOrders:
    def __init__(
        self,
        ports: ListPendingOrdersPorts,
        order_settings: CanalDirectoOrderSettings,
        cache: TTLCache[tuple[int | None, bool], list[PendingOrderRow]] | None = None,
    ) -> None:
        self._ports = ports
        self._order_settings = order_settings
        self._cache = cache

    async def execute(
        self, customer_id: int | None, include_delivered: bool
    ) -> list[PendingOrderRow]:
        if self._cache is None:
            return await self._compute(customer_id, include_delivered)
        return await self._cache.get_or_compute(
            (customer_id, include_delivered),
            lambda: self._compute(customer_id, include_delivered),
        )

    async def _compute(
        self, customer_id: int | None, include_delivered: bool
    ) -> list[PendingOrderRow]:
        """Pega en vivo contra SOAP + Insight (caro) — el caller la envuelve en un
        TTLCache corto (ver ListPendingOrders.__init__) para no recalcular en
        tab-switches/reloads casi simultáneos."""
        orders = await self._ports.processed.get_all_created(customer_id)
        order_by_num = _orders_by_supply_id(orders)
        if not order_by_num:
            return []
        status_by_id = await self._refresh_statuses(order_by_num)
        history_by_id = await self._ports.supply_cache.get_status_history_batch(
            list(order_by_num)
        )
        pending = _in_transit_orders(order_by_num, status_by_id, history_by_id, include_delivered)
        if not pending:
            return []
        return await self._build_rows(pending, status_by_id, history_by_id)

    async def _build_rows(
        self,
        pending: list[tuple[int, ProcessedRequest]],
        status_by_id: dict[int, str],
        history_by_id: dict[int, list[SupplyStatusEvent]],
    ) -> list[PendingOrderRow]:
        """Filas más viejas primero: es justo lo que hay que ir mirando día a día
        antes que lo recién cargado."""
        settings = settings_from_raw(await self._ports.settings.get_all())
        rows, backfill = await PendingOrderRowBuilder(
            self._ports.insight, self._ports.customers, self._order_settings
        ).build(pending, status_by_id, history_by_id, settings)
        if backfill:
            await self._ports.processed.backfill_initial_snapshot(backfill)
        rows.sort(key=lambda r: r.created_at or datetime.min.replace(tzinfo=UTC))
        return rows

    async def _refresh_statuses(
        self, order_by_num: dict[int, ProcessedRequest]
    ) -> dict[int, str]:
        """Estado real en CD, en paralelo y deduplicado. Para los que falló la llamada
        SOAP en vivo, caer al cache local en vez de excluirlos a ciegas (más vale un
        dato levemente viejo que ninguno)."""
        ids = list(order_by_num)
        fresh = await asyncio.gather(*(self._ports.wsayc.fetch_supply_by_id(sid) for sid in ids))
        status_by_id: dict[int, str] = {}
        updates: list[CachedSupply] = []
        for sid, supply in zip(ids, fresh, strict=True):
            if supply is None:
                continue
            status_by_id[sid] = supply.estado
            updates.append(
                CachedSupply(
                    supply_id=sid,
                    serial=order_by_num[sid].device_serial,
                    estado=supply.estado,
                    empresa_id=supply.empresa_id,
                    fecha=parse_cd_datetime(supply.fecha),
                )
            )
        if updates:
            await self._ports.supply_cache.upsert(updates)
        missing = [sid for sid in ids if sid not in status_by_id]
        if missing:
            status_by_id.update(await self._ports.supply_cache.get_statuses_batch(missing))
        return status_by_id


def _orders_by_supply_id(orders: list[ProcessedRequest]) -> dict[int, ProcessedRequest]:
    """{supply_id numérico: orden} — DRYRUN y no parseables quedan afuera (no hay
    pedido real en CD que seguir)."""
    result: dict[int, ProcessedRequest] = {}
    for record in orders:
        if record.internal_order_id.startswith("DRYRUN-"):
            continue
        try:
            result[int(record.internal_order_id.split("-")[0])] = record
        except (ValueError, IndexError):
            continue
    return result


def _in_transit_orders(
    order_by_num: dict[int, ProcessedRequest],
    status_by_id: dict[int, str],
    history_by_id: dict[int, list[SupplyStatusEvent]],
    include_delivered: bool,
) -> list[tuple[int, ProcessedRequest]]:
    cutoff = datetime.now(UTC) - timedelta(days=_DELIVERED_WINDOW_DAYS)
    selected: list[tuple[int, ProcessedRequest]] = []
    for sid, record in order_by_num.items():
        estado = status_by_id.get(sid)
        recently_delivered = (
            include_delivered
            and estado == ENTREGADO
            and _recently_delivered(history_by_id.get(sid, []), cutoff)
        )
        if is_in_transit(estado) or recently_delivered:
            selected.append((sid, record))
    return selected


def _recently_delivered(events: list[SupplyStatusEvent], cutoff: datetime) -> bool:
    for event in reversed(events):
        if event.estado == ENTREGADO:
            return event.first_seen_at >= cutoff
    return False
