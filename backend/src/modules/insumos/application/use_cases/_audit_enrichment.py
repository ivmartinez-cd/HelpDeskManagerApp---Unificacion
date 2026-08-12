"""Enriquecimiento de filas del Historial contra Insight — filas grabadas sin
device_id/initial_* (anteriores a que order_audit capturara esos campos, o
donde la captura falló) se completan en vivo mientras Insight todavía trackee
la solicitud. Separado de list_audit.py por tamaño (ARCHITECTURE_GUIDE §4)."""

import asyncio
import logging

from src.modules.insumos.domain.entities.audit_record import StoredAuditRecord
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict

logger = logging.getLogger(__name__)


async def fetch_tracked_for(
    insight: InsightGateway, records: list[StoredAuditRecord]
) -> dict[int, JsonDict]:
    """Solicitudes que Insight todavía trackea, solo para los clientes de las
    filas que necesitan reparación — {hp_request_id: request}."""
    customer_ids = sorted(
        {
            record.customer_id
            for record in records
            if needs_enrichment(record) and record.customer_id is not None
        }
    )
    if not customer_ids:
        return {}
    batches = await asyncio.gather(*(_fetch_tracked(insight, cid) for cid in customer_ids))
    by_request: dict[int, JsonDict] = {}
    for batch in batches:
        for request in batch:
            by_request.setdefault(int(request["id"]), request)
    return by_request


async def _fetch_tracked(insight: InsightGateway, customer_id: int) -> list[JsonDict]:
    """Mejor esfuerzo: ACTIONED + OUTSTANDING de un cliente; [] si Insight falla
    (la fila queda con "—" como hasta ahora, se reintenta en el próximo GET)."""
    try:
        actioned = await insight.get_consumable_requests(customer_id, workflow_status="ACTIONED")
        outstanding = await insight.get_consumable_requests(
            customer_id, workflow_status="OUTSTANDING"
        )
        return actioned + outstanding
    except Exception as exc:
        logger.warning(
            "list_audit: no se pudo refrescar telemetría de Insight (cliente %s)",
            customer_id,
            exc_info=exc,
        )
        return []


def needs_enrichment(record: StoredAuditRecord) -> bool:
    return (
        record.hp_request_id is not None
        and record.customer_id is not None
        and record.device_id is None
    )
