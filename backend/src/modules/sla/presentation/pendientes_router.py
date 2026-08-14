import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.sla.domain.well_known_permissions import UPDATE, VIEW
from src.modules.sla.infrastructure.repositories.sqlalchemy_prestador_lookup import (
    SqlAlchemyPrestadorLookup,
)
from src.modules.sla.presentation.dependencies import (
    build_get_pendientes_resumen,
    build_list_pendientes,
    build_refresh_pendientes_snapshot,
)
from src.modules.sla.presentation.schemas.pendientes_schemas import (
    IncidenteSinCerrarSchema,
    PendientesResumenResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/sla/pendientes-a-cerrar", tags=["sla-pendientes"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_MAX_PAGE_SIZE = 500


@router.get("/resumen", response_model=PendientesResumenResponse)
async def get_resumen(
    operador_id: uuid.UUID | None = Query(
        default=None,
        alias="operadorId",
        description="Ver los PST de otro operador en vez de los propios",
    ),
    identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> PendientesResumenResponse:
    """Conteo de incidentes pendientes a cerrar por PST — lee el snapshot
    cacheado. Filtra por los PST del operador logueado. Superadmin ve todos."""
    siges_ids_filtro = await _resolver_filtro(db, identity, operador_id)
    result = await build_get_pendientes_resumen(db).execute(siges_ids_filtro=siges_ids_filtro)
    return PendientesResumenResponse.model_validate(result)


@router.get("", response_model=Page[IncidenteSinCerrarSchema])
async def list_pendientes(
    operador_id: uuid.UUID | None = Query(
        default=None,
        alias="operadorId",
        description="Ver los PST de otro operador en vez de los propios",
    ),
    prestador_id: int | None = Query(
        default=None,
        alias="prestadorId",
        description="Filtrar por un PST específico (siges_empresa_id)",
    ),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_MAX_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[IncidenteSinCerrarSchema]:
    """Detalle de incidentes pendientes a cerrar, ordenados por días en estado
    descendente (los más viejos primero).

    Por default filtra a los PST del operador logueado. Un operador sin PST
    asignados no ve nada (lista vacía) — a diferencia de incidentes-vencidos
    donde 'sin PST' devuelve todo, acá es una decisión de negocio explícita."""
    siges_ids_filtro = await _resolver_filtro(db, identity, operador_id)
    if siges_ids_filtro is not None and prestador_id is not None:
        filtro_set = set(siges_ids_filtro)
        if prestador_id not in filtro_set:
            return Page.of([], page=page, size=size)
        siges_ids_filtro = [prestador_id]
    elif prestador_id is not None and siges_ids_filtro is None:
        siges_ids_filtro = [prestador_id]
    dtos = await build_list_pendientes(db).execute(siges_ids_filtro=siges_ids_filtro)
    items = [IncidenteSinCerrarSchema.model_validate(d) for d in dtos]
    return Page.of(items, page=page, size=size)


@router.post("/actualizar", response_model=PendientesResumenResponse)
async def refresh(
    identity: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> PendientesResumenResponse:
    """Fuerza una consulta en vivo a MERCURIO y actualiza el snapshot."""
    await build_refresh_pendientes_snapshot(db).execute()
    siges_ids_filtro = await _resolver_filtro(db, identity, None)
    result = await build_get_pendientes_resumen(db).execute(siges_ids_filtro=siges_ids_filtro)
    return PendientesResumenResponse.model_validate(result)


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
