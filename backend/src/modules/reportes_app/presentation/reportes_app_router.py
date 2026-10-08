"""Reportes de errores y mejoras de la app.

- Alta: botón "Reportar" del header, cualquier usuario logueado.
- Panel (`/admin/reportes`), solo superadmin: ver lo que llegó con la propuesta
  que dejó Claude por el servidor MCP (`scripts/mcp/reportes_app_mcp.py`) y
  aprobarla, pedir cambios o descartarla.

Repo directo, sin use case (ADR-044): inserción, lecturas y una escritura de la
decisión que elige el usuario, sin reglas ni efectos."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.reportes_app.infrastructure.repositories.sqlalchemy_reporte_app_repository import (  # noqa: E501
    SqlAlchemyReporteAppRepository,
)
from src.modules.reportes_app.presentation.foto_storage import FOTOS_DIR, guardar_foto
from src.modules.reportes_app.presentation.schemas import DecisionIn, ReporteOut
from src.shared.domain.errors import NotFoundError, ValidationError
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/reportes-app", tags=["reportes-app"])

_ESTADO_POR_DECISION = {"aprobar": "aprobado", "pedir_cambios": "nuevo", "descartar": "descartado"}
EstadoFiltro = Literal["nuevo", "propuesto", "aprobado", "en_curso", "resuelto", "descartado"]


async def _superadmin(identity: Identity = Depends(get_current_identity)) -> Identity:
    if not identity.user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo para administradores")
    return identity


@router.post("", status_code=status.HTTP_201_CREATED)
async def crear_reporte(
    tipo: Literal["error", "mejora"] = Form(...),
    detalle: str = Form(..., min_length=5, max_length=5000),
    ruta: str = Form(..., max_length=500),
    foto: UploadFile | None = File(default=None),
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> dict[str, uuid.UUID]:
    filename = await guardar_foto(foto) if foto else None
    try:
        reporte_id = await SqlAlchemyReporteAppRepository(db).crear(
            tipo=tipo,
            detalle=detalle.strip(),
            ruta=ruta,
            foto=filename,
            usuario_id=identity.user.id,
        )
    except Exception:  # la inserción falló: no dejar la foto huérfana
        if filename:
            (FOTOS_DIR / filename).unlink(missing_ok=True)
        raise
    return {"id": reporte_id}


@router.get("", response_model=Page[ReporteOut])
async def listar_reportes(
    estado: EstadoFiltro | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _identity: Identity = Depends(_superadmin),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[ReporteOut]:
    items, total = await SqlAlchemyReporteAppRepository(db).listar(
        estado, offset=(page - 1) * size, limit=size
    )
    return Page(items=[ReporteOut.from_vista(v) for v in items], total=total, page=page, size=size)


@router.get("/{reporte_id}/foto")
async def ver_foto(
    reporte_id: uuid.UUID,
    _identity: Identity = Depends(_superadmin),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> FileResponse:
    """Se sirve por id de reporte, nunca por nombre de archivo: sin path traversal."""
    filename = await SqlAlchemyReporteAppRepository(db).nombre_foto(reporte_id)
    if not filename or not (FOTOS_DIR / filename).is_file():
        raise NotFoundError("El reporte no tiene foto")
    return FileResponse(FOTOS_DIR / filename)


@router.post("/{reporte_id}/decision", status_code=status.HTTP_204_NO_CONTENT)
async def decidir_reporte(
    reporte_id: uuid.UUID,
    body: DecisionIn,
    _identity: Identity = Depends(_superadmin),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    respuesta = (body.respuesta or "").strip() or None
    if body.decision == "pedir_cambios" and respuesta is None:
        raise ValidationError("Para pedir cambios, escribí qué querés distinto")
    estado = _ESTADO_POR_DECISION[body.decision]
    if not await SqlAlchemyReporteAppRepository(db).decidir(reporte_id, estado, respuesta):
        raise NotFoundError("No existe el reporte")
