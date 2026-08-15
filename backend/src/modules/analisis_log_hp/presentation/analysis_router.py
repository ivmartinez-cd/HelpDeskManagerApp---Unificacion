"""Router de análisis de logs HP y diagnóstico IA."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.application.use_cases.analyze_log import AnalyzeLog
from src.modules.analisis_log_hp.application.use_cases.diagnose_ai import (
    DiagnoseAi,
    GeneratePdfSummary,
    ListAiModels,
)
from src.modules.analisis_log_hp.application.use_cases.validate_log import ValidateLog
from src.modules.analisis_log_hp.domain.well_known_permissions import VIEW
from src.modules.analisis_log_hp.presentation.dependencies import (
    get_ai_gateway,
    get_error_code_repo,
)
from src.modules.analisis_log_hp.presentation.schemas.analysis_schemas import (
    AiDiagnoseRequest,
    AiDiagnoseResponse,
    AnalysisRequest,
    AnalysisResponse,
    IncidentSchema,
    LogEventSchema,
    ParserErrorSchema,
    ValidateRequest,
    ValidateResponse,
)
from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/analisis-log-hp", tags=["analisis-log-hp"])

_require_view = Depends(require_permission(VIEW))


@router.post("/analysis/preview", response_model=AnalysisResponse)
async def preview_analysis(
    body: AnalysisRequest,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    uc = AnalyzeLog(get_error_code_repo(db))
    result = await uc.execute(body.logs)
    return AnalysisResponse(
        events=[
            LogEventSchema(
                type=e.type, code=e.code, timestamp=e.timestamp, counter=e.counter,
                firmware=e.firmware, help_reference=e.help_reference,
                code_severity=e.code_severity, code_description=e.code_description,
                code_solution_url=e.code_solution_url,
            )
            for e in result.events
        ],
        incidents=[
            IncidentSchema(
                id=i.id, code=i.code, classification=i.classification,
                severity=i.severity, severity_weight=i.severity_weight,
                occurrences=i.occurrences, start_time=i.start_time,
                end_time=i.end_time, counter_range=list(i.counter_range),
                sds_link=i.sds_link,
            )
            for i in result.analysis.incidents
        ],
        global_severity=result.analysis.global_severity,
        events_count=result.analysis.events_count,
        codes_new=result.codes_new,
        errors=[
            ParserErrorSchema(
                line_number=e.line_number, raw_line=e.raw_line, reason=e.reason
            )
            for e in result.report.errors
        ],
    )


@router.post("/analysis/validate", response_model=ValidateResponse)
async def validate_log(
    body: ValidateRequest,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> ValidateResponse:
    uc = ValidateLog(get_error_code_repo(db))
    codes_new = await uc.execute(body.logs)
    return ValidateResponse(codes_new=codes_new)


@router.post("/analysis/ai-diagnose", response_model=AiDiagnoseResponse)
async def ai_diagnose(
    body: AiDiagnoseRequest,
    _: Identity = _require_view,
) -> AiDiagnoseResponse:
    uc = DiagnoseAi(get_ai_gateway())
    result = await uc.execute(body.payload, body.model)
    return AiDiagnoseResponse(
        diagnosis=result.diagnosis, tokens=result.tokens, cost_usd=result.cost_usd
    )


@router.post("/analysis/pdf-summary", response_model=AiDiagnoseResponse)
async def pdf_summary(
    body: AiDiagnoseRequest,
    _: Identity = _require_view,
) -> AiDiagnoseResponse:
    uc = GeneratePdfSummary(get_ai_gateway())
    result = await uc.execute(body.payload, body.model)
    return AiDiagnoseResponse(
        diagnosis=result.diagnosis, tokens=result.tokens, cost_usd=result.cost_usd
    )


@router.get("/analysis/models")
async def list_ai_models(_: Identity = _require_view) -> list[dict[str, Any]]:
    uc = ListAiModels(get_ai_gateway())
    return await uc.execute()
