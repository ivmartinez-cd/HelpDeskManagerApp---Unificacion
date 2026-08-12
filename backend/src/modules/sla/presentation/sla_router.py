from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.sla.application.dtos.sla_dtos import GetSlaComplianceRequest
from src.modules.sla.domain.well_known_permissions import UPDATE, VIEW
from src.modules.sla.presentation.dependencies import (
    build_get_sla_compliance,
    build_list_incidentes_vencidos,
    build_refresh_sla_snapshot,
)
from src.modules.sla.presentation.schemas.sla_schemas import (
    IncidenteVencidoSchema,
    SlaResumenResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/sla", tags=["sla"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
# Un mes ronda los ~450 incidentes en total y muchos menos vencidos; si un
# período llegara a superar esto, subir el tope antes que silenciar la
# paginación (mismo criterio que el calendario de contadores).
_MAX_PAGE_SIZE = 500
_periodo = Query(..., ge=200001, le=210012, description="Período mensual AAAAMM, ej. 202608")


@router.get("/resumen", response_model=SlaResumenResponse)
async def get_resumen(
    periodo: int = _periodo,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> SlaResumenResponse:
    """Cumplimiento del período (Correcto vs. Vencido) + desglose de vencidos
    por técnico/PST — lee el snapshot cacheado, no consulta MERCURIO en vivo
    salvo cold start (ver GetSlaCompliance)."""
    use_case = build_get_sla_compliance(db)
    result = await use_case.execute(GetSlaComplianceRequest(periodo=periodo))
    return SlaResumenResponse.model_validate(result)


@router.get("/incidentes-vencidos", response_model=Page[IncidenteVencidoSchema])
async def list_incidentes_vencidos(
    periodo: int = _periodo,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_MAX_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[IncidenteVencidoSchema]:
    """Detalle de los incidentes vencidos del período, para la tabla agrupada
    por técnico de la pantalla de SLA."""
    dtos = await build_list_incidentes_vencidos(db).execute(periodo)
    items = [IncidenteVencidoSchema.model_validate(d) for d in dtos]
    return Page.of(items, page=page, size=size)


@router.post("/actualizar", response_model=SlaResumenResponse)
async def refresh_resumen(
    periodo: int = _periodo,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> SlaResumenResponse:
    """Fuerza una consulta en vivo a MERCURIO y guarda el snapshot nuevo —
    mismo camino que corre el job de fondo cada SLA_REFRESH_INTERVAL_MINUTES,
    pero a demanda desde el botón "Actualizar" de la pantalla de SLA."""
    await build_refresh_sla_snapshot(db).execute(periodo)
    use_case = build_get_sla_compliance(db)
    result = await use_case.execute(GetSlaComplianceRequest(periodo=periodo))
    return SlaResumenResponse.model_validate(result)
