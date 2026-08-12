"""Caso de uso GetAuditSummary — los conteos por evento de las 5 pestañas del
Historial (GET /api/insumos/audit/summary). Sin enriquecimiento contra Insight:
solo agrega sobre order_audit."""

from dataclasses import dataclass

from src.modules.insumos.application.dtos.audit_query import ListAuditQuery, to_summary_filters
from src.modules.insumos.application.dtos.audit_summary import AuditSummary
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.value_objects.audit_history import ORDER_EVENTS, SYSTEM_EVENTS


@dataclass(frozen=True)
class GetAuditSummaryPorts:
    audit: OrderAuditRepository


class GetAuditSummary:
    def __init__(self, ports: GetAuditSummaryPorts) -> None:
        self._ports = ports

    async def execute(self, query: ListAuditQuery) -> AuditSummary:
        """El `scope` de la query se ignora a propósito: el resumen siempre
        cuenta todos los eventos, el frontend suma según la pestaña activa."""
        by_event = await self._ports.audit.count_by_event(to_summary_filters(query))
        orders = sum(by_event.get(event, 0) for event in ORDER_EVENTS)
        system = sum(by_event.get(event, 0) for event in SYSTEM_EVENTS)
        return AuditSummary(by_event=by_event, orders=orders, system=system, total=orders + system)
