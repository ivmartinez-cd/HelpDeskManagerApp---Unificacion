import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.sla.domain.well_known_permissions import VIEW
from src.modules.sla.infrastructure.repositories.sqlalchemy_prestador_lookup import (
    SqlAlchemyPrestadorLookup,
)
from src.modules.sla.presentation.dependencies import build_list_incidentes_derivados
from src.modules.sla.presentation.schemas.derivados_schemas import IncidenteDerivadoSchema
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/sla/incidentes-derivados", tags=["sla-derivados"])

_require_view = Depends(require_permission(VIEW))
_MAX_PAGE_SIZE = 500
_periodo = Query(..., ge=200001, le=210012, description="Período mensual AAAAMM, ej. 202608")
_operador_id = Query(
    default=None,
    alias="operadorId",
    description="Ver los PST de otro operador en vez de los propios",
)


@router.get("", response_model=Page[IncidenteDerivadoSchema])
async def list_incidentes_derivados(
    periodo: int = _periodo,
    operador_id: uuid.UUID | None = _operador_id,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_MAX_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[IncidenteDerivadoSchema]:
    """Incidentes de PST del interior en estado Derivado (200) del período,
    ordenados por días desde el ingreso descendente (los más viejos primero).

    Por default filtra a los PST del operador logueado. Superadmin sin
    operadorId ve todos. Consulta en vivo, sin snapshot."""
    siges_ids_filtro = await _resolver_filtro(db, identity, operador_id)
    dtos = await build_list_incidentes_derivados(db).execute(
        periodo, siges_ids_filtro=siges_ids_filtro
    )
    items = [IncidenteDerivadoSchema.model_validate(d) for d in dtos]
    return Page.of(items, page=page, size=size)


async def _resolver_filtro(
    db: AsyncSession,
    identity: Identity,
    operador_id: uuid.UUID | None,
) -> list[int] | None:
    if identity.user.is_superadmin and operador_id is None:
        return None
    lookup = SqlAlchemyPrestadorLookup(db)
    target = operador_id if operador_id is not None else identity.user.id
    return await lookup.get_siges_ids_por_operador(target)
