"""Endpoints de equipos descubiertos en SDS que todavía nadie registró."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.domain.well_known_permissions import UPDATE, VIEW
from src.modules.insumos.presentation.dependencies import (
    build_count_new_devices,
    build_dismiss_new_device,
    build_list_new_devices,
    build_sync_new_devices,
)
from src.modules.insumos.presentation.schemas.new_device_schemas import (
    DismissDeviceResponse,
    DismissRequestBody,
    NewDeviceRowOut,
    NewDevicesSummaryOut,
    SyncNewDevicesResponse,
)
from src.shared.domain.errors import NotFoundError
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))


@router.get("/new-devices", response_model=Page[NewDeviceRowOut])
async def list_new_devices(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=500),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[NewDeviceRowOut]:
    """Equipos sin monitorear de clientes habilitados (no generan avisos de insumos),
    más nuevo primero. Default de `size` generoso como en /requests: la tabla muestra
    todo y filtra client-side, pero el contrato sigue paginado. El contador de
    pendientes vive en /new-devices/summary."""
    rows = await build_list_new_devices(db).execute()
    return Page.of([NewDeviceRowOut.from_row(r) for r in rows], page=page, size=size)


@router.get("/new-devices/summary", response_model=NewDevicesSummaryOut)
async def new_devices_summary(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> NewDevicesSummaryOut:
    """Solo el contador de pendientes sin ignorar — el badge de la barra lateral."""
    return NewDevicesSummaryOut(pending_count=await build_count_new_devices(db).execute())


@router.patch("/new-devices/{device_id}", response_model=DismissDeviceResponse)
async def set_device_dismissed(
    device_id: int,
    body: DismissRequestBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> DismissDeviceResponse:
    """Marca o desmarca un equipo como ignorado (p.ej. equipos fuera de contrato)."""
    if not await build_dismiss_new_device(db).execute(device_id, body.dismissed):
        raise NotFoundError(f"No existe el equipo {device_id}")
    return DismissDeviceResponse(ok=True)


@router.post("/new-devices/sync", response_model=SyncNewDevicesResponse)
async def sync_new_devices(
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SyncNewDevicesResponse:
    """Fuerza la sincronización del inventario contra la Insight API. Es la misma
    operación que corre el poller: refresca clientes, detecta equipos nuevos y poda
    los que Insight ya no devuelve."""
    return SyncNewDevicesResponse.from_result(await build_sync_new_devices(db).execute())
