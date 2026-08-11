"""Caso de uso ListPendingOrders — port de compute_pending_orders (pending_orders.py):
pedidos cargados por esta app (processed_requests, CREATED) que siguen circulando en
Canal Directo, para seguir día a día cómo evoluciona el consumo y el ciclo
Pendiente→Remito Generado→Despachado→Entregado hasta que se despachen.

Deliberadamente independiente de /requests: no tiene nada que ver con las alertas
OUTSTANDING/ACTIONED de Insight (esas se resuelven o desaparecen de Insight por su
cuenta antes de que el pedido físico llegue — mezclar ambos conceptos fue el bug de la
primera versión en el legacy). Acá solo importan nuestros pedidos y su estado real en CD.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.modules.insumos.application.dtos.pending_orders import PendingOrderRow
from src.modules.insumos.domain.entities.processed_request import (
    ProcessedInitialSnapshot,
    ProcessedRequest,
)
from src.modules.insumos.domain.repositories.customer_config_repository import (
    CustomerConfigRepository,
)
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.repositories.insumos_settings_repository import (
    InsumosSettingsRepository,
)
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.services.request_status import status_for_days_left
from src.modules.insumos.domain.value_objects.cd_datetime import parse_cd_datetime
from src.modules.insumos.domain.value_objects.cd_state import ENTREGADO, is_in_transit
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, SupplyStatusEvent
from src.modules.insumos.domain.value_objects.insumos_settings import (
    InsumosSettings,
    settings_from_raw,
)
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings

logger = logging.getLogger(__name__)

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
        self, ports: ListPendingOrdersPorts, order_settings: CanalDirectoOrderSettings
    ) -> None:
        self._ports = ports
        self._order_settings = order_settings

    async def execute(
        self, customer_id: int | None, include_delivered: bool
    ) -> list[PendingOrderRow]:
        """Filas más viejas primero: es justo lo que hay que ir mirando día a día
        antes que lo recién cargado."""
        settings = settings_from_raw(await self._ports.settings.get_all())
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
        rows = await self._build_rows(pending, status_by_id, history_by_id, settings)
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

    async def _build_rows(
        self,
        pending: list[tuple[int, ProcessedRequest]],
        status_by_id: dict[int, str],
        history_by_id: dict[int, list[SupplyStatusEvent]],
        settings: InsumosSettings,
    ) -> list[PendingOrderRow]:
        names = await self._ports.customers.get_names()
        devices = await self._fetch_devices({record.device_id for _, record in pending})
        current_by_request = await self._fetch_current(
            {record.customer_id for _, record in pending}
        )
        rows: list[PendingOrderRow] = []
        backfill: list[ProcessedInitialSnapshot] = []
        for sid, record in pending:
            current = current_by_request.get(record.hp_request_id)
            rows.append(
                self._row_from(
                    sid, record, status_by_id[sid], history_by_id.get(sid, []),
                    names, devices, current, settings, backfill,
                )
            )
        if backfill:
            await self._ports.processed.backfill_initial_snapshot(backfill)
        return rows

    async def _fetch_devices(self, device_ids: set[int | None]) -> dict[int, JsonDict]:
        """Best-effort: un fallo puntual al buscar un equipo (Insight caído/timeout)
        no debe tirar toda la respuesta — ese pedido queda con store="" en vez de
        romper."""

        async def fetch(device_id: int) -> tuple[int, JsonDict]:
            try:
                return device_id, await self._ports.insight.get_device_by_id(device_id)
            except Exception as exc:
                logger.warning(
                    "list_pending_orders: no se pudo obtener el equipo %s",
                    device_id,
                    exc_info=exc,
                )
                return device_id, {}

        ids = sorted(did for did in device_ids if did is not None)
        return dict(await asyncio.gather(*(fetch(did) for did in ids)))

    async def _fetch_current(self, customer_ids: set[int | None]) -> dict[int, JsonDict]:
        """Lectura ACTUAL de Insight, mejor esfuerzo: mientras la solicitud siga en
        OUTSTANDING o ACTIONED, Insight sigue actualizando percentLeft/daysLeft/
        pagesLeft — el "¿cómo evolucionó desde que cargamos?" del seguimiento. Si ya
        no aparece en ninguna de las dos, current_* queda None — no se inventa nada."""

        async def fetch(customer_id: int) -> list[JsonDict]:
            try:
                outstanding = await self._ports.insight.get_consumable_requests(
                    customer_id, workflow_status="OUTSTANDING"
                )
                actioned = await self._ports.insight.get_consumable_requests(
                    customer_id, workflow_status="ACTIONED"
                )
                return outstanding + actioned
            except Exception as exc:
                logger.error(
                    "list_pending_orders: no se pudo refrescar telemetría de Insight "
                    "(cliente %s)",
                    customer_id,
                    exc_info=exc,
                )
                return []

        ids = sorted(cid for cid in customer_ids if cid is not None)
        batches = await asyncio.gather(*(fetch(cid) for cid in ids))
        return {int(r["id"]): r for batch in batches for r in batch}

    def _row_from(
        self,
        sid: int,
        record: ProcessedRequest,
        estado: str,
        history: list[SupplyStatusEvent],
        names: dict[int, str],
        devices: dict[int, JsonDict],
        current: JsonDict | None,
        settings: InsumosSettings,
        backfill: list[ProcessedInitialSnapshot],
    ) -> PendingOrderRow:
        consumable = (current or {}).get("consumable") or {}
        current_days_left = consumable.get("daysLeft")
        status_key = status_label = None
        if current_days_left is not None:
            status_key, status_label = status_for_days_left(int(current_days_left), settings)
        initial = _initial_snapshot(record, current, backfill)
        device = devices.get(record.device_id or 0, {})
        return PendingOrderRow(
            hp_request_id=record.hp_request_id,
            customer_id=record.customer_id or 0,
            customer_name=names.get(record.customer_id or 0),
            device_id=record.device_id or 0,
            serial=record.device_serial,
            store=str((device.get("extendedFields") or {}).get("zone") or ""),
            sku=record.sku,
            description=record.description,
            order_id=record.internal_order_id,
            supply_url=self._order_settings.supply_web_url(sid),
            supply_status=estado,
            created_at=record.created_at,
            initial_percent_left=initial[0],
            initial_days_left=initial[1],
            initial_pages_left=initial[2],
            current_percent_left=consumable.get("percentLeft"),
            current_days_left=current_days_left,
            current_pages_left=consumable.get("pagesLeft"),
            status_key=status_key,
            status_label=status_label,
            status_history=history,
        )


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


def _initial_snapshot(
    record: ProcessedRequest,
    current: JsonDict | None,
    backfill: list[ProcessedInitialSnapshot],
) -> tuple[int | None, int | None, int | None]:
    """Pedidos cargados antes de que processed_requests guardara la foto inicial:
    completarla con requestedLevel/requestedDaysLeft — el valor que Insight registra
    AL MOMENTO de tramitar la solicitud, no consumable.percentLeft (la lectura ACTUAL,
    que sigue bajando — usarla acá haría que inicial y actual salieran siempre
    iguales, tapando el seguimiento que es todo el sentido de esta pantalla). No hay
    campo equivalente de páginas al momento de la solicitud — queda None."""
    if record.initial_percent_left is not None or current is None:
        return (
            record.initial_percent_left,
            record.initial_days_left,
            record.initial_pages_left,
        )
    percent = current.get("requestedLevel")
    days = current.get("requestedDaysLeft")
    if percent is not None:
        backfill.append(
            ProcessedInitialSnapshot(
                hp_request_id=record.hp_request_id,
                initial_percent_left=percent,
                initial_days_left=days,
                initial_pages_left=None,
            )
        )
    return percent, days, None
