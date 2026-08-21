"""Endpoints de detalle de equipo/consumible (modal de detalle del dashboard) — port
de los reads de routers/requests/query.py que no son el listado principal."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.domain.well_known_permissions import VIEW
from src.modules.insumos.presentation.dependencies import (
    build_get_availability_windows,
    build_get_consumable_detail,
    build_get_consumable_history,
    build_get_consumable_request_history,
    build_get_device_supplies,
)
from src.modules.insumos.presentation.schemas.device_schemas import (
    AvailabilityWindowOut,
    AvailabilityWindowsResponse,
    ConsumableDetailOut,
    ConsumableHistoryPointOut,
    ConsumableHistoryResponse,
    ConsumableRequestHistoryItemOut,
    ConsumableRequestHistoryResponse,
    DeviceSuppliesResponse,
    DeviceSupplyItemOut,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/insumos/devices", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))


@router.get("/{serial}/supplies", response_model=DeviceSuppliesResponse)
async def get_device_supplies(
    serial: str,
    limit: int = Query(default=3, ge=1, le=20),
    dry_run: bool = Query(default=False, alias="dryRun"),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> DeviceSuppliesResponse:
    """Últimos `limit` pedidos de insumos en Canal Directo para la serie dada
    (SOAP + cache local + pedidos propios). Con dryRun=true solo se loguea la
    consulta — el SOAP es read-only, no se crea nada."""
    rows = await build_get_device_supplies(db).execute(serial, limit=limit, dry_run=dry_run)
    return DeviceSuppliesResponse(
        serial=serial.strip().upper(),
        supplies=[DeviceSupplyItemOut.from_row(r) for r in rows],
        dry_run=dry_run,
    )


@router.get(
    "/{device_id}/consumables/{index}/history", response_model=ConsumableHistoryResponse
)
async def get_consumable_history(
    device_id: int,
    index: int,
    _: Identity = _require_view,
) -> ConsumableHistoryResponse:
    """Historial de nivel de UN consumible puntual (~12 meses) — el gráfico del modal."""
    points = await build_get_consumable_history().execute(device_id, index)
    return ConsumableHistoryResponse(
        points=[ConsumableHistoryPointOut.from_point(p) for p in points]
    )


@router.get(
    "/{device_id}/consumables/{index}/requests",
    response_model=ConsumableRequestHistoryResponse,
)
async def get_consumable_request_history(
    device_id: int,
    index: int,
    customer_id: int = Query(alias="customerId"),
    _: Identity = _require_view,
) -> ConsumableRequestHistoryResponse:
    """Historial de TODAS las solicitudes de HP SDS para este consumible puntual
    (los 6 workflowStatus, como la tabla del portal)."""
    rows = await build_get_consumable_request_history().execute(device_id, index, customer_id)
    return ConsumableRequestHistoryResponse(
        items=[ConsumableRequestHistoryItemOut.from_row(r) for r in rows]
    )


@router.get("/{device_id}/availability-windows", response_model=AvailabilityWindowsResponse)
async def get_device_availability_windows(
    device_id: int,
    _: Identity = _require_view,
) -> AvailabilityWindowsResponse:
    """Ventanas de "sin contacto" del EQUIPO — la franja sobre el gráfico de nivel."""
    windows = await build_get_availability_windows().execute(device_id)
    return AvailabilityWindowsResponse(
        windows=[AvailabilityWindowOut.from_window(w) for w in windows]
    )


@router.get("/{device_id}/consumables/{index}/detail", response_model=ConsumableDetailOut)
async def get_consumable_detail(
    device_id: int,
    index: int,
    _: Identity = _require_view,
) -> ConsumableDetailOut:
    """Datos ampliados EN VIVO de un consumible puntual — 404 si no existe en Insight."""
    result = await build_get_consumable_detail().execute(device_id, index)
    return ConsumableDetailOut.from_result(result)
