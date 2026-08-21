"""Endpoints de solicitudes: dashboard, listado y acciones (load/cancel/dismiss/reconcile)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.application.dtos.load_order import LoadOrderCommand
from src.modules.insumos.application.dtos.request_actions import DismissCommand, ReconcileCommand
from src.modules.insumos.domain.well_known_permissions import CREATE, VIEW
from src.modules.insumos.presentation.dependencies import (
    build_cancel_order,
    build_dismiss_request,
    build_get_dashboard,
    build_list_pending_orders,
    build_list_requests,
    build_load_order,
    build_reconcile_order,
)
from src.modules.insumos.presentation.schemas.action_schemas import (
    CancelResponse,
    DismissRequestBody,
    DismissResponse,
    ReconcileRequestBody,
    ReconcileResponse,
)
from src.modules.insumos.presentation.schemas.dashboard_schemas import DashboardResponse
from src.modules.insumos.presentation.schemas.load_schemas import LoadRequestBody, LoadResponse
from src.modules.insumos.presentation.schemas.pending_order_schemas import PendingOrderRowOut
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
    db: AsyncSession = Depends(get_db, scope="function"),
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
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[RequestRowOut]:
    """Solicitudes OUTSTANDING (de un cliente o de todos los habilitados), enriquecidas
    con equipo, severidad, validación y el pedido asociado en CD. El default de `size`
    es generoso a propósito: la tabla del dashboard muestra todo y filtra client-side
    (mismo criterio que los catálogos de contadores) — el contrato sigue paginado."""
    rows = await build_list_requests(db).execute(customer_id)
    return Page.of([RequestRowOut.from_row(r) for r in rows], page=page, size=size)


@router.get("/orders/pending", response_model=Page[PendingOrderRowOut])
async def list_pending_orders(
    customer_id: int | None = Query(default=None, alias="customerId"),
    include_delivered: bool = Query(default=False, alias="includeDelivered"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=500),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[PendingOrderRowOut]:
    """Pedidos propios que siguen circulando en Canal Directo (seguimiento día a día),
    más viejos primero. Mismo criterio de `size` generoso que /requests: la pestaña
    muestra todo y filtra client-side — el contrato sigue paginado."""
    rows = await build_list_pending_orders(db).execute(customer_id, include_delivered)
    return Page.of([PendingOrderRowOut.from_row(r) for r in rows], page=page, size=size)


@router.post("/requests/{request_id}/load", response_model=LoadResponse)
async def load_request(
    request_id: int,
    body: LoadRequestBody,
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
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


@router.post("/requests/{request_id}/cancel", response_model=CancelResponse)
async def cancel_request(
    request_id: int,
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> CancelResponse:
    """Anula en Canal Directo el pedido asociado y libera el registro local.
    Responde 200 siempre; errores de negocio como ok=false + error."""
    result = await build_cancel_order(db).execute(request_id)
    return CancelResponse.from_result(result)


@router.post("/requests/{request_id}/dismiss", response_model=DismissResponse)
async def dismiss_request(
    request_id: int,
    body: DismissRequestBody,
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> DismissResponse:
    """Descarta la solicitud directamente en HP SDS (status_update=DELETE)."""
    command = DismissCommand(
        hp_request_id=request_id,
        customer_id=body.customer_id,
        customer_name=body.customer_name,
        device_serial=body.serial,
        sku=body.sku,
    )
    result = await build_dismiss_request(db).execute(command)
    return DismissResponse.from_result(result)


@router.post("/requests/{request_id}/reconcile", response_model=ReconcileResponse)
async def reconcile_request(
    request_id: int,
    body: ReconcileRequestBody,
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ReconcileResponse:
    """Vincula un pedido que ya existe en Canal Directo pero que la app no registró
    como propio (verificación post-creación fallida). Nunca crea un pedido nuevo."""
    command = ReconcileCommand(
        hp_request_id=request_id,
        customer_id=body.customer_id,
        customer_name=body.customer_name,
    )
    result = await build_reconcile_order(db).execute(command)
    return ReconcileResponse.from_result(result)
