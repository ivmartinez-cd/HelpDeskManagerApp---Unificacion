"""Completa `consumable_serial` en pedidos ya cargados que se quedaron sin ese dato
(creados antes de que se empezara a guardar, o por un hipo de red puntual al crearse) —
port de consumable_serial_backfill.py. Reconsulta la solicitud original en Insight
(por customer_id, agrupado para minimizar llamadas) y matchea por hp_request_id.

Dos usos: chequeo periódico del poller (últimos 7 días, ver poller.py) y script manual
de todo el historial (backend/scripts/backfill_consumable_serial.py)."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)

logger = logging.getLogger(__name__)

_WORKFLOW_STATUSES = ("ACTIONED", "COMPLETED")


@dataclass(frozen=True)
class BackfillConsumableSerialPorts:
    insight: InsightGateway
    processed: ProcessedRequestRepository


class BackfillConsumableSerial:
    def __init__(self, ports: BackfillConsumableSerialPorts) -> None:
        self._ports = ports

    async def execute(self, within_days: int | None = None) -> int:
        missing = await self._ports.processed.get_missing_consumable_serial(within_days)
        if not missing:
            return 0
        by_customer: dict[int, list[ProcessedRequest]] = {}
        for row in missing:
            if row.customer_id is not None:
                by_customer.setdefault(row.customer_id, []).append(row)
        results = await asyncio.gather(
            *(
                self._fetch_for_customer(customer_id, rows)
                for customer_id, rows in by_customer.items()
            )
        )
        updates = [pair for batch in results for pair in batch]
        if updates:
            await self._ports.processed.backfill_consumable_serial(updates)
        return len(updates)

    async def _fetch_for_customer(
        self, customer_id: int, rows: list[ProcessedRequest]
    ) -> list[tuple[int, str]]:
        wanted = {r.hp_request_id for r in rows}
        from_date, to_date = _date_bounds(rows)
        found: dict[int, str] = {}
        for status in _WORKFLOW_STATUSES:
            requests = await self._fetch_status(customer_id, status, from_date, to_date)
            _collect_serials(requests, wanted, found)
        return list(found.items())

    async def _fetch_status(
        self, customer_id: int, status: str, from_date: str | None, to_date: str | None
    ) -> list[JsonDict]:
        try:
            return await self._ports.insight.get_consumable_requests(
                customer_id, workflow_status=status, from_date=from_date, to_date=to_date
            )
        except Exception as exc:
            logger.warning(
                "backfill_consumable_serial: falló %s para cliente %s",
                status,
                customer_id,
                exc_info=exc,
            )
            return []


def _collect_serials(requests: list[JsonDict], wanted: set[int], found: dict[int, str]) -> None:
    for req in requests:
        req_id = req.get("id")
        if req_id not in wanted or req_id in found:
            continue
        serial = (req.get("consumable") or {}).get("serialNumber")
        if serial:
            found[req_id] = serial


def _date_bounds(rows: list[ProcessedRequest]) -> tuple[str | None, str | None]:
    """±1 día de margen sobre min/max created_at — cubre el desfase entre el día que se
    creó el pedido y el día que Insight registró la solicitud original."""
    dates = [r.created_at for r in rows if r.created_at is not None]
    if not dates:
        return None, None
    start = min(dates) - timedelta(days=1)
    end = max(dates) + timedelta(days=1)
    return start.strftime("%Y-%m-%dT00:00:00Z"), end.strftime("%Y-%m-%dT23:59:59Z")
