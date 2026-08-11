"""Endpoints de la auditoría de equipos offline y su baja en el PortalWeb de SDS."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.domain.value_objects.offline_clock import calendar_days_offline
from src.modules.insumos.domain.well_known_permissions import DELETE, UPDATE, VIEW
from src.modules.insumos.presentation.dependencies.offline_devices import (
    build_count_offline_candidates,
    build_delete_offline_devices,
    build_dismiss_offline_device,
    build_list_offline_devices,
    build_list_offline_outages,
    build_verify_offline_devices,
)
from src.modules.insumos.presentation.schemas.offline_action_schemas import (
    DeleteBody,
    DeleteResponse,
    OfflineDismissBody,
    OfflineDismissResponse,
    VerifyBody,
    VerifyResponse,
)
from src.modules.insumos.presentation.schemas.offline_device_schemas import (
    MassOutageOut,
    OfflineDeviceOut,
    OfflineSummaryOut,
)
from src.modules.insumos.presentation.wiring import app_timezone
from src.shared.domain.errors import NotFoundError
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_require_delete = Depends(require_permission(DELETE))


@router.get("/offline-devices", response_model=Page[OfflineDeviceOut])
async def list_offline_devices(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=500),
    customer_id: int | None = Query(default=None, alias="customerId"),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[OfflineDeviceOut]:
    """Equipos offline con su veredicto de Canal Directo y estado de outage."""
    uc = await build_list_offline_devices(db)
    devices, snapshot = await uc.execute(customer_id)
    now = datetime.now(UTC)
    tz = app_timezone()
    rows = [
        OfflineDeviceOut.from_device(
            d,
            in_mass_outage=d.device_id in snapshot.outage_device_ids,
            deletable=d.device_id in snapshot.deletable_ids,
            days_offline=calendar_days_offline(d.last_contact, now, tz),
        )
        for d in devices
    ]
    return Page.of(rows, page=page, size=size)


@router.get("/offline-devices/outages", response_model=Page[MassOutageOut])
async def list_offline_outages(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=100, ge=1, le=500),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[MassOutageOut]:
    """Caídas de colector y salidas masivas detectadas en el inventario actual."""
    uc = await build_list_offline_outages(db)
    outages = await uc.execute()
    return Page.of([MassOutageOut.from_outage(o) for o in outages], page=page, size=size)


@router.get("/offline-devices/summary", response_model=OfflineSummaryOut)
async def offline_devices_summary(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> OfflineSummaryOut:
    """Contador de candidatos a baja — usado por el badge de la barra lateral."""
    uc = await build_count_offline_candidates(db)
    return OfflineSummaryOut(candidate_count=await uc.execute())


@router.post("/offline-devices/verify", response_model=VerifyResponse)
async def verify_offline_devices(
    body: VerifyBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> VerifyResponse:
    """Consulta Canal Directo (SOAP) para los equipos pendientes de re-verificación.
    limit obligatorio (le=50) para mantener la duración del request acotada.
    Si ya hay una verificación en curso responde 409."""
    uc = await build_verify_offline_devices(db)
    summary = await uc.execute(limit=body.limit, customer_id=body.customer_id)
    return VerifyResponse.from_summary(summary)


@router.patch("/offline-devices/{device_id}", response_model=OfflineDismissResponse)
async def set_offline_dismissed(
    device_id: int,
    body: OfflineDismissBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> OfflineDismissResponse:
    """Marca o desmarca un equipo como descartado de la vista offline."""
    if not await build_dismiss_offline_device(db).execute(device_id, body.dismissed):
        raise NotFoundError(f"No existe el equipo {device_id}")
    return OfflineDismissResponse(ok=True)


@router.post("/offline-devices/delete", response_model=DeleteResponse)
async def delete_offline_devices(
    body: DeleteBody,
    _: Identity = _require_delete,
    db: AsyncSession = Depends(get_db),
) -> DeleteResponse:
    """Da de baja los equipos seleccionados en el PortalWeb de SDS.

    Solo equipos con veredicto BODEGA y sin outage son candidatos válidos — el resto
    se rechaza server-side. Si ya hay una baja en curso responde 409.
    SDS_DELETE_DRY_RUN=true (default): audita pero no llama al portal ni borra la fila.
    """
    if not body.device_ids:
        raise HTTPException(status_code=400, detail="No se seleccionó ningún equipo")
    uc = await build_delete_offline_devices(db)
    result = await uc.execute(body.device_ids)
    return DeleteResponse.from_result(result)
