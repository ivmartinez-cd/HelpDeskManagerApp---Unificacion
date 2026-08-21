"""Construcción de filas de ListPendingOrders: enriquecimiento con datos de
equipo y telemetría en vivo de Insight, más el backfill de la foto inicial —
separado de list_pending_orders.py porque ese archivo ya superaba el tamaño
máximo de archivo (§4). Read-only a propósito: el caller persiste el backfill
que devuelve `build()`."""

import asyncio
import logging

from src.modules.insumos.application.dtos.pending_orders import PendingOrderRow
from src.modules.insumos.domain.entities.processed_request import (
    ProcessedInitialSnapshot,
    ProcessedRequest,
)
from src.modules.insumos.domain.repositories.customer_config_repository import (
    CustomerConfigRepository,
)
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.services.request_status import status_for_days_left
from src.modules.insumos.domain.value_objects.cd_supply import SupplyStatusEvent
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings

logger = logging.getLogger(__name__)


class PendingOrderRowBuilder:
    def __init__(
        self,
        insight: InsightGateway,
        customers: CustomerConfigRepository,
        order_settings: CanalDirectoOrderSettings,
    ) -> None:
        self._insight = insight
        self._customers = customers
        self._order_settings = order_settings

    async def build(
        self,
        pending: list[tuple[int, ProcessedRequest]],
        status_by_id: dict[int, str],
        history_by_id: dict[int, list[SupplyStatusEvent]],
        settings: InsumosSettings,
    ) -> tuple[list[PendingOrderRow], list[ProcessedInitialSnapshot]]:
        names = await self._customers.get_names()
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
        return rows, backfill

    async def _fetch_devices(self, device_ids: set[int | None]) -> dict[int, JsonDict]:
        """Best-effort: un fallo puntual al buscar un equipo (Insight caído/timeout)
        no debe tirar toda la respuesta — ese pedido queda con store="" en vez de
        romper."""

        async def fetch(device_id: int) -> tuple[int, JsonDict]:
            try:
                return device_id, await self._insight.get_device_by_id(device_id)
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
                outstanding = await self._insight.get_consumable_requests(
                    customer_id, workflow_status="OUTSTANDING"
                )
                actioned = await self._insight.get_consumable_requests(
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
