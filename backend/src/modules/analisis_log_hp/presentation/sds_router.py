"""Router de integración con HP SDS/Insight (extracción de logs, datos en vivo)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.application.use_cases.extract_sds_logs import ExtractSdsLogs
from src.modules.analisis_log_hp.application.use_cases.get_device_live_data import (
    GetClientDevices,
    GetDeviceAlerts,
    GetDeviceConsumables,
    GetDeviceMeters,
)
from src.modules.analisis_log_hp.application.use_cases.get_hp_operations import GetHpOperations
from src.modules.analisis_log_hp.application.use_cases.get_remote_ews import GetRemoteEws
from src.modules.analisis_log_hp.application.use_cases.refresh_hp_cache import RefreshHpCache
from src.modules.analisis_log_hp.application.use_cases.resolve_device import ResolveDevice
from src.modules.analisis_log_hp.domain.well_known_permissions import VIEW
from src.modules.analisis_log_hp.presentation.dependencies import (
    get_error_code_repo,
    get_hp_insight_gateway,
    get_hp_portal_gateway,
)
from src.modules.analisis_log_hp.presentation.schemas.analysis_schemas import (
    SdsExtractRequest,
    SdsExtractResponse,
)
from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/analisis-log-hp/sds", tags=["analisis-log-hp"])

_require_view = Depends(require_permission(VIEW))


@router.post("/extract-logs", response_model=SdsExtractResponse)
async def extract_logs(
    body: SdsExtractRequest,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> SdsExtractResponse:
    uc = ExtractSdsLogs(get_hp_portal_gateway(), get_error_code_repo(db))
    result = await uc.execute(body.serial, days=body.days)
    return SdsExtractResponse(
        device_id=result.device_id,
        model_name=result.model_name,
        tsv=result.tsv,
        help_urls_updated=result.help_urls_updated,
    )


@router.get("/resolve-device")
async def resolve_device(
    serial: str = Query(...),
    _: Identity = _require_view,
) -> dict[str, Any] | None:
    uc = ResolveDevice(get_hp_insight_gateway())
    return await uc.execute(serial)


@router.get("/devices/{device_id}/consumables")
async def get_consumables(
    device_id: int,
    _: Identity = _require_view,
) -> list[dict[str, Any]]:
    uc = GetDeviceConsumables(get_hp_insight_gateway())
    return await uc.execute(device_id)


@router.get("/devices/{device_id}/alerts")
async def get_alerts(
    device_id: int,
    current_only: bool = Query(default=True),
    _: Identity = _require_view,
) -> list[dict[str, Any]]:
    uc = GetDeviceAlerts(get_hp_insight_gateway())
    return await uc.execute(device_id, current_only=current_only)


@router.get("/devices/{device_id}/meters")
async def get_meters(
    device_id: int,
    days: int = Query(default=90, ge=1, le=365),
    _: Identity = _require_view,
) -> list[dict[str, Any]]:
    uc = GetDeviceMeters(get_hp_insight_gateway())
    return await uc.execute(device_id, days=days)


@router.get("/devices/{device_id}/remote-ews")
async def get_remote_ews(
    device_id: str,
    _: Identity = _require_view,
) -> dict[str, str | None]:
    uc = GetRemoteEws(get_hp_portal_gateway())
    url = await uc.execute(device_id)
    return {"url": url}


@router.get("/devices/{device_id}/hp-operations")
async def get_hp_operations(
    device_id: str,
    _: Identity = _require_view,
) -> list[dict[str, Any]]:
    uc = GetHpOperations(get_hp_portal_gateway())
    return await uc.execute(device_id)


@router.post("/devices/{device_id}/refresh-cache")
async def refresh_hp_cache(
    device_id: str,
    _: Identity = _require_view,
) -> dict[str, Any]:
    uc = RefreshHpCache(get_hp_portal_gateway())
    baseline = await uc.execute(device_id)
    return {"baseline": baseline}


@router.get("/clients/{customer_id}/devices")
async def get_client_devices(
    customer_id: int,
    _: Identity = _require_view,
) -> list[dict[str, Any]]:
    uc = GetClientDevices(get_hp_insight_gateway())
    return await uc.execute(customer_id)
