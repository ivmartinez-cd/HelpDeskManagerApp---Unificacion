"""Caso de uso GetConsumableRequestHistory — port de GET /api/devices/{id}/consumables/
{index}/requests: TODAS las solicitudes de HP SDS para un consumible puntual — no solo
las OUTSTANDING/ACTIONED "vivas" que usa el resto de la app, sino también QUERIED/
IGNORED/DELETED/COMPLETED (mismo dato que la tabla 'Historial de solicitudes de
consumibles' del portal). Insight no deja filtrar por deviceId del lado del servidor,
así que hay que pedir cada workflowStatus por separado (una sola vez, para este
cliente) y filtrar acá."""

import asyncio

from src.modules.insumos.application.dtos.device_detail import ConsumableRequestHistoryRow
from src.modules.insumos.application.use_cases._insight_history_range import (
    history_datetime_range,
)
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict

# Todos los estados que puede tener una solicitud de consumible en Insight — el
# historial del modal necesita los 6 para reconstruir la misma tabla que el portal HP.
_ALL_WORKFLOW_STATUSES = ("OUTSTANDING", "QUERIED", "ACTIONED", "IGNORED", "DELETED", "COMPLETED")

# `status` en la respuesta (NEW/DELETED/ACTIONED/COMPLETED/IGNORED/QUERIED) no es
# directamente el workflowStatus pedido (OUTSTANDING → NEW) — mapeo a lo que muestra
# el portal.
_REQUEST_STATUS_LABELS = {
    "NEW": "Nuevo",
    "DELETED": "Eliminado",
    "ACTIONED": "Actuada",
    "COMPLETED": "Completada",
    "IGNORED": "Ignorada",
    "QUERIED": "Consultada",
}


class GetConsumableRequestHistory:
    def __init__(self, insight: InsightGateway) -> None:
        self._insight = insight

    async def execute(
        self, device_id: int, index: int, customer_id: int
    ) -> list[ConsumableRequestHistoryRow]:
        """Filas más reciente primero. Un fallo de Insight propaga (→ 502): con un
        workflowStatus faltante la tabla mentiría por omisión."""
        from_date, to_date = history_datetime_range()
        batches = await asyncio.gather(
            *(
                self._insight.get_consumable_requests(
                    customer_id, workflow_status=status, from_date=from_date, to_date=to_date
                )
                for status in _ALL_WORKFLOW_STATUSES
            )
        )
        rows = self._filter_rows(batches, device_id, index)
        rows.sort(key=lambda r: r.requested, reverse=True)
        return rows

    def _filter_rows(
        self, batches: list[list[JsonDict]], device_id: int, index: int
    ) -> list[ConsumableRequestHistoryRow]:
        seen_ids: set[int] = set()
        rows: list[ConsumableRequestHistoryRow] = []
        for batch in batches:
            for request in batch:
                consumable = request.get("consumable") or {}
                if (
                    request.get("deviceId") != device_id
                    or request["id"] in seen_ids
                    or consumable.get("index") != index
                ):
                    continue
                seen_ids.add(request["id"])
                rows.append(_row_from(request))
        return rows


def _row_from(request: JsonDict) -> ConsumableRequestHistoryRow:
    status = str(request.get("status") or "")
    return ConsumableRequestHistoryRow(
        request_id=int(request["id"]),
        requested=str(request.get("requested") or ""),
        status=status,
        status_label=_REQUEST_STATUS_LABELS.get(status, status),
        reason=request.get("reason"),
        requested_level=request.get("requestedLevel"),
        requested_days_left=request.get("requestedDaysLeft"),
    )
