"""Router de manuales de servicio CPMD (PDF por familia de modelo HP)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.application.use_cases.cpmd import (
    FindCpmdManual,
    GetCpmdManualById,
    UploadCpmdManual,
)
from src.modules.analisis_log_hp.domain.well_known_permissions import VIEW
from src.modules.analisis_log_hp.presentation.cpmd_storage import cpmd_dir, save_cpmd_pdf
from src.modules.analisis_log_hp.presentation.dependencies import get_cpmd_manual_repo
from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/analisis-log-hp/cpmd", tags=["analisis-log-hp"])

_require_view = Depends(require_permission(VIEW))


@router.get("/pdf-url")
async def get_pdf_url(
    model_family: str = Query(...),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> dict[str, str]:
    uc = FindCpmdManual(get_cpmd_manual_repo(db))
    manual = await uc.execute(model_family)
    if not manual:
        raise HTTPException(404, "No hay manual CPMD cargado para este modelo")
    return {"url": f"/api/analisis-log-hp/cpmd/{manual.id}/file", "label": manual.label}


@router.post("/upload", status_code=201)
async def upload_manual(
    file: UploadFile = File(...),
    keywords: str = Form(...),
    label: str = Form(...),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> dict[str, int]:
    filename = await save_cpmd_pdf(file)
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    uc = UploadCpmdManual(get_cpmd_manual_repo(db))
    manual = await uc.execute(keywords=kw_list, label=label, filename=filename)
    return {"id": manual.id}


@router.get("/{manual_id}/file")
async def get_manual_file(
    manual_id: int,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> FileResponse:
    uc = GetCpmdManualById(get_cpmd_manual_repo(db))
    manual = await uc.execute(manual_id)
    if not manual:
        raise HTTPException(404, "Manual CPMD no encontrado")
    path = cpmd_dir() / manual.filename
    if not path.is_file():
        raise HTTPException(404, "Archivo del manual CPMD no encontrado en disco")
    return FileResponse(path, media_type="application/pdf", filename=f"{manual.label}.pdf")
