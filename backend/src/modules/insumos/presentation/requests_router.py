"""POST /api/insumos/requests/{request_id}/load — creación de pedidos en Canal Directo."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.application.dtos.load_order import LoadOrderCommand
from src.modules.insumos.domain.well_known_permissions import CREATE, VIEW
from src.modules.insumos.presentation.dependencies import build_get_dashboard, build_load_order
from src.modules.insumos.presentation.schemas.dashboard_schemas import DashboardResponse
from src.modules.insumos.presentation.schemas.load_schemas import LoadRequestBody, LoadResponse
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db

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
