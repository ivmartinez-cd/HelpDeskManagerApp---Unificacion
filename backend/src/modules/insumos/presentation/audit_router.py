"""Endpoints del Historial: listado (GET /api/insumos/audit) y resumen de
badges por pestaña (GET /api/insumos/audit/summary) — permanente, filtrado y
paginado en SQL."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.application.dtos.audit_query import ListAuditQuery
from src.modules.insumos.domain.well_known_permissions import VIEW
from src.modules.insumos.presentation.dependencies import (
    build_get_audit_summary,
    build_list_audit,
)
from src.modules.insumos.presentation.schemas.audit_schemas import AuditRowOut
from src.modules.insumos.presentation.schemas.audit_summary_schemas import AuditSummaryResponse
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))


def audit_query(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=100, ge=1, le=1000),
    scope: Literal["orders", "system", "all"] = Query(default="all"),
    event: list[str] | None = Query(default=None),
    start_date: date | None = Query(default=None, alias="startDate"),
    end_date: date | None = Query(default=None, alias="endDate"),
    search: str | None = Query(default=None, max_length=200),
) -> ListAuditQuery:
    """Parseo compartido entre /audit y /audit/summary — misma pinta de
    filtros para ambos. `event` es múltiple (?event=RELEASED&event=CANCELLED,
    la opción combinada "Anulado / liberado" del frontend); se valida contra
    KNOWN_EVENTS en el dominio, no acá."""
    return ListAuditQuery(
        page=page,
        size=size,
        scope=scope,
        events=tuple(event) if event else (),
        start_day=start_date,
        end_day=end_date,
        search=search,
    )


@router.get("/audit", response_model=Page[AuditRowOut])
async def list_audit(
    query: ListAuditQuery = Depends(audit_query),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[AuditRowOut]:
    """Historial permanente de eventos (pedidos y acciones del sistema), más
    reciente primero. Filtrado y paginado en SQL — la tabla nunca se poda."""
    rows, total = await build_list_audit(db).execute(query)
    return Page(
        items=[AuditRowOut.from_row(r) for r in rows], total=total, page=query.page, size=query.size
    )


@router.get("/audit/summary", response_model=AuditSummaryResponse)
async def audit_summary(
    query: ListAuditQuery = Depends(audit_query),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> AuditSummaryResponse:
    """Conteo por evento (y agregado por pestaña) para los badges del
    Historial — ignora `scope`, siempre cuenta todos los eventos."""
    summary = await build_get_audit_summary(db).execute(query)
    return AuditSummaryResponse.from_summary(summary)
