from fastapi import APIRouter, Depends, Query

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.sla.application.dtos.sla_dtos import GetSlaComplianceRequest
from src.modules.sla.application.use_cases.get_sla_compliance import GetSlaCompliance
from src.modules.sla.application.use_cases.list_incidentes_vencidos import (
    ListIncidentesVencidos,
)
from src.modules.sla.domain.well_known_permissions import VIEW
from src.modules.sla.presentation.dependencies import get_sla_query_gateway
from src.modules.sla.presentation.schemas.sla_schemas import (
    IncidenteVencidoSchema,
    SlaResumenResponse,
)
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/sla", tags=["sla"])

_require_view = Depends(require_permission(VIEW))
# Un mes ronda los ~450 incidentes en total y muchos menos vencidos; si un
# período llegara a superar esto, subir el tope antes que silenciar la
# paginación (mismo criterio que el calendario de contadores).
_MAX_PAGE_SIZE = 500
_periodo = Query(..., ge=200001, le=210012, description="Período mensual AAAAMM, ej. 202608")


@router.get("/resumen", response_model=SlaResumenResponse)
async def get_resumen(
    periodo: int = _periodo,
    _: Identity = _require_view,
) -> SlaResumenResponse:
    """Cumplimiento del período (Correcto vs. Vencido) + desglose de vencidos
    por técnico/PST — el reemplazo de la tabla dinámica de Excel manual."""
    use_case = GetSlaCompliance(get_sla_query_gateway())
    result = await use_case.execute(GetSlaComplianceRequest(periodo=periodo))
    return SlaResumenResponse.model_validate(result)


@router.get("/incidentes-vencidos", response_model=Page[IncidenteVencidoSchema])
async def list_incidentes_vencidos(
    periodo: int = _periodo,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_MAX_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_view,
) -> Page[IncidenteVencidoSchema]:
    """Detalle de los incidentes vencidos del período, para la tabla agrupada
    por técnico de la pantalla de SLA."""
    dtos = await ListIncidentesVencidos(get_sla_query_gateway()).execute(periodo)
    items = [IncidenteVencidoSchema.model_validate(d) for d in dtos]
    return Page.of(items, page=page, size=size)
