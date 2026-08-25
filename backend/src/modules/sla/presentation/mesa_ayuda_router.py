from fastapi import APIRouter, Depends, Query

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.sla.domain.well_known_permissions import VIEW
from src.modules.sla.presentation.dependencies import build_list_incidentes_mesa_ayuda
from src.modules.sla.presentation.schemas.mesa_ayuda_schemas import IncidenteMesaAyudaSchema
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/sla/mesa-de-ayuda", tags=["sla-mesa-ayuda"])

_require_view = Depends(require_permission(VIEW))
_MAX_PAGE_SIZE = 500


@router.get("", response_model=Page[IncidenteMesaAyudaSchema])
async def list_incidentes_mesa_ayuda(
    operador: str | None = Query(
        default=None,
        description="Filtrar por login del último operador que modificó el incidente",
    ),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_MAX_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    identity: Identity = _require_view,
) -> Page[IncidenteMesaAyudaSchema]:
    """Incidentes de Siges asignados a 'CD - Mesa de Ayuda' que siguen sin
    cerrar, ordenados por días transcurridos descendente (los más viejos
    primero). Consulta en vivo, sin snapshot."""
    dtos = await build_list_incidentes_mesa_ayuda().execute(operador_login=operador)
    items = [IncidenteMesaAyudaSchema.model_validate(d) for d in dtos]
    return Page.of(items, page=page, size=size)
