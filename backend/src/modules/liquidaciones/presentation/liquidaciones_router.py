"""Endpoints de liquidaciones — listado, importación, detalle y reanálisis.

`/importar` está registrado ANTES de `/{liquidacion_id}` a propósito: FastAPI matchea
rutas en orden de registro, y si `/{liquidacion_id}` fuera primero, un POST a
`/importar` intentaría parsear "importar" como UUID y devolvería 422 en vez de llegar
al handler correcto."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.liquidaciones.domain.well_known_permissions import CREATE, UPDATE, VIEW
from src.modules.liquidaciones.presentation.dependencies import (
    build_get_liquidacion_detalle,
    build_importar_liquidacion,
    build_list_liquidaciones,
    build_reanalizar_liquidacion,
)
from src.modules.liquidaciones.presentation.schemas.importar_liquidacion_schemas import (
    ImportarLiquidacionOut,
)
from src.modules.liquidaciones.presentation.schemas.liquidacion_detalle_schemas import (
    LiquidacionDetalleOut,
)
from src.modules.liquidaciones.presentation.schemas.liquidacion_schemas import LiquidacionOut
from src.modules.liquidaciones.presentation.schemas.reanalizar_liquidacion_schemas import (
    ReanalizarLiquidacionOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_require_create = Depends(require_permission(CREATE))


@router.get("", response_model=Page[LiquidacionOut])
async def list_liquidaciones(
    prestador_id: UUID = Query(alias="prestadorId"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[LiquidacionOut]:
    liquidaciones = await build_list_liquidaciones(db).execute(prestador_id)
    return Page.of(
        [LiquidacionOut.from_entity(item) for item in liquidaciones], page=page, size=size
    )


@router.post("/importar", response_model=ImportarLiquidacionOut, status_code=201)
async def importar_liquidacion(
    file: UploadFile = File(...),
    prestador_id: UUID = Form(alias="prestadorId"),
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db),
) -> ImportarLiquidacionOut:
    contenido = await file.read()
    resultado = await build_importar_liquidacion(db).execute(
        prestador_id=prestador_id, contenido=contenido, nombre_archivo=file.filename or ""
    )
    return ImportarLiquidacionOut.from_dto(resultado)


@router.get("/{liquidacion_id}", response_model=LiquidacionDetalleOut)
async def get_liquidacion_detalle(
    liquidacion_id: UUID,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> LiquidacionDetalleOut:
    detalle = await build_get_liquidacion_detalle(db).execute(liquidacion_id)
    return LiquidacionDetalleOut.from_dto(detalle)


@router.post("/{liquidacion_id}/reanalyze", response_model=ReanalizarLiquidacionOut)
async def reanalyze_liquidacion(
    liquidacion_id: UUID,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> ReanalizarLiquidacionOut:
    resultado = await build_reanalizar_liquidacion(db).execute(liquidacion_id)
    return ReanalizarLiquidacionOut.from_dto(resultado)
