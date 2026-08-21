"""Router del catálogo de códigos de error HP."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.application.use_cases.get_solution_proxy import (
    GetSolutionProxy,
)
from src.modules.analisis_log_hp.application.use_cases.upsert_error_code import UpsertErrorCode
from src.modules.analisis_log_hp.domain.well_known_permissions import VIEW
from src.modules.analisis_log_hp.presentation.dependencies import (
    get_error_code_repo,
    get_hp_portal_gateway,
)
from src.modules.analisis_log_hp.presentation.schemas.error_code_schemas import (
    ErrorCodeSchema,
    UpsertErrorCodeRequest,
)
from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/analisis-log-hp/error-codes", tags=["analisis-log-hp"])

_require_view = Depends(require_permission(VIEW))


@router.get("", response_model=Page[ErrorCodeSchema])
async def list_error_codes(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[ErrorCodeSchema]:
    repo = get_error_code_repo(db)
    result = await repo.list_page(page, size)
    return Page(
        items=[ErrorCodeSchema(**ec.__dict__) for ec in result.items],
        total=result.total,
        page=result.page,
        size=result.size,
    )


@router.post("/upsert", response_model=ErrorCodeSchema)
async def upsert_error_code(
    body: UpsertErrorCodeRequest,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ErrorCodeSchema:
    uc = UpsertErrorCode(get_error_code_repo(db), get_hp_portal_gateway())
    result = await uc.execute(
        body.code,
        severity=body.severity,
        description=body.description,
        solution_url=body.solution_url,
    )
    return ErrorCodeSchema(**result.__dict__)


@router.get("/{code}/solution-proxy")
async def solution_proxy(
    code: str,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> dict[str, Any]:
    uc = GetSolutionProxy(get_error_code_repo(db), get_hp_portal_gateway())
    content = await uc.execute(code)
    return {"code": code, "content": content}
