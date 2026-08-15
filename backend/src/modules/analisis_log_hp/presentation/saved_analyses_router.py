"""Router de análisis guardados, comparación y salud del equipo."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.application.use_cases.analyze_log import AnalyzeLog
from src.modules.analisis_log_hp.application.use_cases.saved_analyses import (
    CompareAnalysisWithLog,
    CompareSnapshots,
    CreateSavedAnalysis,
    DeleteSavedAnalysis,
    GetAnalysisHealth,
    GetSavedAnalysis,
    ListSavedAnalyses,
    UpdateSavedAnalysis,
)
from src.modules.analisis_log_hp.domain.well_known_permissions import VIEW
from src.modules.analisis_log_hp.presentation.dependencies import (
    get_error_code_repo,
    get_saved_analysis_repo,
    get_telemetry_repo,
)
from src.modules.analisis_log_hp.presentation.schemas.saved_analysis_schemas import (
    CompareLogsRequest,
    CreateSavedAnalysisRequest,
    DeviceHealthResponse,
    SavedAnalysisDetailResponse,
    SavedAnalysisResponse,
)
from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(
    prefix="/api/analisis-log-hp/saved-analyses", tags=["analisis-log-hp"]
)

_require_view = Depends(require_permission(VIEW))


def _saved_to_response(s: Any) -> SavedAnalysisResponse:
    return SavedAnalysisResponse(
        id=s.id, name=s.name, equipment_identifier=s.equipment_identifier,
        global_severity=s.global_severity, created_at=s.created_at,
    )


def _saved_to_detail(s: Any) -> SavedAnalysisDetailResponse:
    return SavedAnalysisDetailResponse(
        id=s.id, name=s.name, equipment_identifier=s.equipment_identifier,
        global_severity=s.global_severity, created_at=s.created_at,
        incidents=s.incidents, ai_diagnosis=s.ai_diagnosis,
    )


@router.get("", response_model=Page[SavedAnalysisResponse])
async def list_saved_analyses(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[SavedAnalysisResponse]:
    uc = ListSavedAnalyses(get_saved_analysis_repo(db))
    result = await uc.execute(page, size)
    return Page(
        items=[_saved_to_response(s) for s in result.items],
        total=result.total, page=result.page, size=result.size,
    )


@router.post("", response_model=SavedAnalysisDetailResponse, status_code=201)
async def create_saved_analysis(
    body: CreateSavedAnalysisRequest,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> SavedAnalysisDetailResponse:

    from src.modules.analisis_log_hp.domain.entities.incident import Incident
    incidents = [
        Incident(
            id=i.id, code=i.code, classification=i.classification,
            severity=i.severity, severity_weight=i.severity_weight,
            occurrences=i.occurrences, start_time=i.start_time,
            end_time=i.end_time, counter_range=(i.counter_range[0], i.counter_range[1]),
            sds_link=i.sds_link,
        )
        for i in body.incidents
    ]
    uc = CreateSavedAnalysis(get_saved_analysis_repo(db), get_telemetry_repo(db))
    saved = await uc.execute(
        body.name, body.equipment_identifier, incidents,
        body.global_severity, body.ai_diagnosis,
    )
    return _saved_to_detail(saved)


@router.get("/{id}", response_model=SavedAnalysisDetailResponse)
async def get_saved_analysis(
    id: UUID,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> SavedAnalysisDetailResponse:
    uc = GetSavedAnalysis(get_saved_analysis_repo(db))
    return _saved_to_detail(await uc.execute(id))


@router.put("/{id}", response_model=SavedAnalysisDetailResponse)
async def update_saved_analysis(
    id: UUID,
    body: CreateSavedAnalysisRequest,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> SavedAnalysisDetailResponse:
    from src.modules.analisis_log_hp.domain.entities.incident import Incident
    incidents = [
        Incident(
            id=i.id, code=i.code, classification=i.classification,
            severity=i.severity, severity_weight=i.severity_weight,
            occurrences=i.occurrences, start_time=i.start_time,
            end_time=i.end_time, counter_range=(i.counter_range[0], i.counter_range[1]),
            sds_link=i.sds_link,
        )
        for i in body.incidents
    ]
    uc = UpdateSavedAnalysis(get_saved_analysis_repo(db), get_telemetry_repo(db))
    saved = await uc.execute(
        id, body.equipment_identifier, incidents,
        body.global_severity, body.ai_diagnosis,
    )
    return _saved_to_detail(saved)


@router.delete("/{id}", status_code=204)
async def delete_saved_analysis(
    id: UUID,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> None:
    uc = DeleteSavedAnalysis(get_saved_analysis_repo(db), get_telemetry_repo(db))
    await uc.execute(id)


@router.post("/{id}/compare")
async def compare_with_log(
    id: UUID,
    body: CompareLogsRequest,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    analyze_uc = AnalyzeLog(get_error_code_repo(db))
    analyze_result = await analyze_uc.execute(body.logs)
    compare_uc = CompareAnalysisWithLog(get_saved_analysis_repo(db))
    result = await compare_uc.execute(
        id,
        list(analyze_result.analysis.incidents),
        analyze_result.analysis.global_severity,
        analyze_result.analysis.events_count,
    )
    return {
        "saved": _saved_to_detail(result.saved).model_dump(mode="json"),
        "current": {
            "incidents": result.current_incidents,
            "global_severity": result.current_global_severity,
            "events_count": result.current_events_count,
        },
        "diff": result.diff,
    }


@router.get("/{id}/compare-with/{target_id}")
async def compare_two_snapshots(
    id: UUID,
    target_id: UUID,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    uc = CompareSnapshots(get_saved_analysis_repo(db))
    result = await uc.execute(id, target_id)
    return {
        "older": _saved_to_detail(result["older"]).model_dump(mode="json"),
        "newer": _saved_to_detail(result["newer"]).model_dump(mode="json"),
        "diff": result["diff"],
    }


@router.get("/{id}/health", response_model=DeviceHealthResponse)
async def get_device_health(
    id: UUID,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> DeviceHealthResponse:
    uc = GetAnalysisHealth(get_saved_analysis_repo(db), get_telemetry_repo(db))
    result = await uc.execute(id)
    return DeviceHealthResponse(
        status=result.health.status,
        label=result.health.label,
        reason=result.health.reason,
        recommendation=result.health.recommendation,
        triggered_rule=result.health.triggered_rule,
        events_count=result.events_count,
    )
