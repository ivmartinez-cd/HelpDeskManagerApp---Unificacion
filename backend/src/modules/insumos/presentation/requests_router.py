"""POST /api/insumos/requests/{request_id}/load — creación de pedidos en Canal Directo."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.application.dtos.load_order import LoadOrderCommand
from src.modules.insumos.domain.well_known_permissions import CREATE, VIEW
from src.modules.insumos.presentation.dependencies import (
    build_get_dashboard,
    build_list_requests,
    build_load_order,
)
from src.modules.insumos.presentation.schemas.dashboard_schemas import DashboardResponse
from src.modules.insumos.presentation.schemas.load_schemas import LoadRequestBody, LoadResponse
from src.modules.insumos.presentation.schemas.request_row_schemas import RequestRowOut
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))
_require_create = Depends(require_permission(CREATE))


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """Resumen global de solicitudes pendientes de todos los clientes habilitados."""
    result = await build_get_dashboard(db).execute(
        refresh_minutes=get_settings().poll_interval_minutes
    )
    return DashboardResponse.from_result(result)


@router.get("/requests", response_model=Page[RequestRowOut])
async def list_requests(
    customer_id: int | None = Query(default=None, alias="customerId"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=500),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[RequestRowOut]:
    """Solicitudes OUTSTANDING (de un cliente o de todos los habilitados), enriquecidas
    con equipo, severidad, validación y el pedido asociado en CD. El default de `size`
    es generoso a propósito: la tabla del dashboard muestra todo y filtra client-side
    (mismo criterio que los catálogos de contadores) — el contrato sigue paginado."""
    rows = await build_list_requests(db).execute(customer_id)
    return Page.of([RequestRowOut.from_row(r) for r in rows], page=page, size=size)


@router.post("/requests/{request_id}/load", response_model=LoadResponse)
async def load_request(
    request_id: int,
    body: LoadRequestBody,
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db),
) -> LoadResponse:
    """Crea el pedido para la solicitud dada. Responde 200 siempre: los errores de
    negocio viajan como ok=false (+error/conflictType), igual que en el legacy."""
    command = LoadOrderCommand(
        hp_request_id=request_id,
        customer_id=body.customer_id,
        customer_name=body.customer_name,
        dry_run=body.dry_run,
        force_override=body.force_override,
        override_insumo_id=body.override_insumo_id,
        revision=body.revision,
    )
    result = await build_load_order(db).execute(command)
    return LoadResponse.from_result(result)
