"""Caso de uso ListAudit — port de GET /api/audit (routers/audit.py), el Historial.

Además de listar, repara filas grabadas sin device_id/initial_* (anteriores a que
order_audit capturara esos campos, o donde la captura falló — van a entrar también
con la importación de datos del legacy): mientras Insight todavía trackee la
solicitud (ACTIONED u OUTSTANDING) se completan en vivo y se persisten (backfill)
para no repetir el lookup en cada GET. Si Insight ya no sabe nada de ella (caso
normal con el tiempo), la fila queda como está — no se inventa un valor.
"""

from dataclasses import dataclass

from src.modules.insumos.application.dtos.audit_query import ListAuditQuery, to_filters
from src.modules.insumos.application.dtos.audit_rows import AuditRow
from src.modules.insumos.application.use_cases._audit_enrichment import (
    fetch_tracked_for,
    needs_enrichment,
)
from src.modules.insumos.domain.entities.audit_record import (
    ORDER_TYPE_INCIDENT,
    AuditSnapshot,
    StoredAuditRecord,
)
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway, JsonDict
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.services.audit_history_rules import action_for
from src.modules.insumos.domain.value_objects.audit_history import AuditClosures
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings

_DRYRUN_PREFIX = "DRYRUN-"


@dataclass(frozen=True)
class ListAuditPorts:
    audit: OrderAuditRepository
    insight: InsightGateway


class ListAudit:
    def __init__(self, ports: ListAuditPorts, order_settings: CanalDirectoOrderSettings) -> None:
        self._ports = ports
        self._order_settings = order_settings

    async def execute(self, query: ListAuditQuery) -> tuple[list[AuditRow], int]:
        """(filas de la página, total) — más reciente primero."""
        filters = to_filters(query)
        total = await self._ports.audit.count(filters)
        offset = (query.page - 1) * query.size
        records = await self._ports.audit.list_page(filters, query.size, offset)
        closures = await self._ports.audit.closures_for(
            [r.hp_request_id for r in records if r.hp_request_id is not None]
        )
        tracked = await fetch_tracked_for(self._ports.insight, records)
        rows: list[AuditRow] = []
        backfill: list[AuditSnapshot] = []
        for record in records:
            rows.append(self._row_from(record, tracked, backfill, closures))
        if backfill:
            await self._ports.audit.backfill_snapshots(backfill)
        return rows, total

    def _row_from(
        self,
        record: StoredAuditRecord,
        tracked: dict[int, JsonDict],
        backfill: list[AuditSnapshot],
        closures: AuditClosures,
    ) -> AuditRow:
        device_id = record.device_id
        percent, days, pages = (
            record.initial_percent_left,
            record.initial_days_left,
            record.initial_pages_left,
        )
        insight_request = (
            tracked.get(record.hp_request_id)
            if needs_enrichment(record) and record.hp_request_id is not None
            else None
        )
        if insight_request is not None:
            device_id = insight_request.get("deviceId")
            # requestedLevel/requestedDaysLeft: el valor AL MOMENTO de tramitar la
            # solicitud — no consumable.percentLeft, que es la lectura de HOY y haría
            # que "% al cargar" muestre el nivel actual. Sin equivalente de páginas.
            percent = insight_request.get("requestedLevel")
            days = insight_request.get("requestedDaysLeft")
            pages = None
            if device_id is not None:
                backfill.append(
                    AuditSnapshot(
                        audit_id=record.audit_id,
                        device_id=int(device_id),
                        initial_percent_left=percent,
                        initial_days_left=days,
                        initial_pages_left=None,
                    )
                )
        return AuditRow(
            audit_id=record.audit_id,
            event=record.event,
            created_at=record.created_at,
            hp_request_id=record.hp_request_id,
            device_id=device_id,
            customer_id=record.customer_id,
            customer_name=record.customer_name,
            device_serial=record.device_serial,
            sku=record.sku,
            description=record.description,
            internal_order_id=record.internal_order_id,
            order_type=record.order_type,
            detail=record.detail,
            dry_run=record.dry_run,
            hp_request_time=record.hp_request_time,
            initial_percent_left=percent,
            initial_days_left=days,
            initial_pages_left=pages,
            supply_url=self._supply_url_for(record.order_type, record.internal_order_id),
            action=action_for(record, closures),
        )

    def _supply_url_for(self, order_type: str, internal_order_id: str | None) -> str | None:
        """Link al portal para el pedido/incidente; None si es dry-run o no parseable."""
        if not internal_order_id or internal_order_id.startswith(_DRYRUN_PREFIX):
            return None
        if order_type == ORDER_TYPE_INCIDENT:
            return f"{self._order_settings.portal_base_url}/incidents/view/{internal_order_id}"
        try:
            supply_id = int(internal_order_id.split("-")[0])
        except (ValueError, IndexError):
            return None
        return self._order_settings.supply_web_url(supply_id)
