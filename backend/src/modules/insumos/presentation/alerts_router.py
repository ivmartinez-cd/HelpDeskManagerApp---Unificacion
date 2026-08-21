"""Endpoints de alertas de solicitudes pendientes sin cargar."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.domain.well_known_permissions import UPDATE, VIEW
from src.modules.insumos.presentation.dependencies import (
    build_acknowledge_alerts,
    build_list_alerts,
)
from src.modules.insumos.presentation.schemas.alert_schemas import (
    AcknowledgeRequestBody,
    AcknowledgeResponse,
    AlertRowOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))


@router.get("/alerts", response_model=Page[AlertRowOut])
async def list_alerts(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=200, ge=1, le=500),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[AlertRowOut]:
    """Alertas escaladas sin reconocer, la más antigua primero. Escala las vencidas al
    momento — el `total` del envelope es el `escalatedCount` del legacy."""
    alerts = await build_list_alerts(db).execute()
    return Page.of([AlertRowOut.from_alert(a) for a in alerts], page=page, size=size)


@router.post("/alerts/ack", response_model=AcknowledgeResponse)
async def acknowledge_alerts(
    body: AcknowledgeRequestBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AcknowledgeResponse:
    """Reconoce a mano una o varias alertas escaladas (el operario ya las está
    gestionando pero todavía no puede cargar el pedido)."""
    count = await build_acknowledge_alerts(db).execute(body.hp_request_ids)
    return AcknowledgeResponse(ok=True, acknowledged=count)
