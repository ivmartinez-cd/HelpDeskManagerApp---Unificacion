"""Schema del resumen del Historial (GET /api/insumos/audit/summary).

En snake_case (`by_event`, `orders`, `system`, `total`) — consistente con
AuditRowOut, que ya es snake_case por contrato legacy. A diferencia de
Estadísticas (camelCase con serialization_alias), acá no hay legacy que
respetar y gana la consistencia con la pantalla que ya existe."""

from pydantic import BaseModel

from src.modules.insumos.application.dtos.audit_summary import AuditSummary


class AuditSummaryResponse(BaseModel):
    by_event: dict[str, int]
    orders: int
    system: int
    total: int

    @classmethod
    def from_summary(cls, summary: AuditSummary) -> "AuditSummaryResponse":
        return cls(
            by_event=summary.by_event,
            orders=summary.orders,
            system=summary.system,
            total=summary.total,
        )
