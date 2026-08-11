"""Caso de uso SyncMonitorStatus — refresca dca_monitors con el estado real de Insight.

Port de sync_monitor_status del legacy (offline_devices.py). Reemplaza el
ThreadPoolExecutor con asyncio.Semaphore + gather: la Insight API REST es paralela
(a diferencia del wsAyC SOAP, que es secuencial y pausado a propósito).

Error por cliente se loguea y se saltea — nunca aborta el lote completo.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.insumos.domain.repositories.dca_monitor_repository import DcaMonitorRepository
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.value_objects.dca_monitor import DcaMonitorStatus

logger = logging.getLogger(__name__)

_MAX_CONCURRENT = 8


@dataclass(frozen=True)
class SyncMonitorStatusPorts:
    insight: InsightGateway
    monitors: DcaMonitorRepository


class SyncMonitorStatus:
    def __init__(self, ports: SyncMonitorStatusPorts) -> None:
        self._ports = ports

    async def execute(self, customer_ids: set[int]) -> int:
        """Refresca el estado de los colectores de los clientes dados. Devuelve la
        cantidad de entradas upserted."""
        if not customer_ids:
            return 0
        sem = asyncio.Semaphore(_MAX_CONCURRENT)
        tasks = [self._fetch(sem, cid) for cid in customer_ids]
        results = await asyncio.gather(*tasks)
        entries = [e for batch in results for e in batch]
        if entries:
            await self._ports.monitors.upsert(entries)
        return len(entries)

    async def _fetch(
        self, sem: asyncio.Semaphore, customer_id: int
    ) -> list[DcaMonitorStatus]:
        async with sem:
            try:
                monitors = await self._ports.insight.get_monitors(customer_id)
            except Exception as exc:
                logger.warning(
                    "sync_monitor_status: error al traer monitores del cliente %d",
                    customer_id,
                    extra={"customer_id": customer_id},
                    exc_info=exc,
                )
                return []
        now = datetime.now(UTC)
        return [
            DcaMonitorStatus(
                customer_id=customer_id,
                monitor_name=entry.get("name") or "",
                online=bool(entry.get("online")),
                status=entry.get("status") or "",
                last_contact=_parse_contact(entry),
                checked_at=now,
            )
            for entry in monitors
            if entry.get("name")
        ]


def _parse_contact(entry: JsonDict) -> datetime | None:
    raw = entry.get("lastContact")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
