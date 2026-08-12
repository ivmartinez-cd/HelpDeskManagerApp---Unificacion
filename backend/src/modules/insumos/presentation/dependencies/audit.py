"""Factories del Historial (GET /api/insumos/audit y /audit/summary)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases.get_audit_summary import (
    GetAuditSummary,
    GetAuditSummaryPorts,
)
from src.modules.insumos.application.use_cases.list_audit import ListAudit, ListAuditPorts
from src.modules.insumos.infrastructure.repositories.sqlalchemy_order_audit_repository import (
    SqlAlchemyOrderAuditRepository,
)
from src.modules.insumos.presentation.wiring import get_insight_gateway, order_settings
from src.shared.infrastructure.config.settings import get_settings


def build_list_audit(session: AsyncSession) -> ListAudit:
    ports = ListAuditPorts(
        audit=SqlAlchemyOrderAuditRepository(session),
        insight=get_insight_gateway(),
    )
    return ListAudit(ports, order_settings(get_settings()))


def build_get_audit_summary(session: AsyncSession) -> GetAuditSummary:
    ports = GetAuditSummaryPorts(audit=SqlAlchemyOrderAuditRepository(session))
    return GetAuditSummary(ports)
