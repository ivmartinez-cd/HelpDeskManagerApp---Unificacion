"""Endpoints de configuración de prestadores (/api/liquidaciones/prestadores)."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.presentation import _liq_csv as csv_helpers
from src.modules.liquidaciones.presentation import _liq_csv_export as csv_export
from src.modules.liquidaciones.presentation.config_routers._deps import (
    require_export,
    require_update,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_create_prestador,
    build_delete_prestador,
    build_importar_prestador_maestro,
    build_toggle_prestador_activo,
    build_update_prestador,
)
from src.modules.liquidaciones.presentation.schemas.config_schemas import (
    PrestadorIn,
    PrestadorOut,
    ToggleActivoIn,
    VincularBaseSucursalIn,
    VincularCdIn,
)
from src.modules.liquidaciones.presentation.schemas.importar_prestador_maestro_schemas import (
    ImportarPrestadorMaestroOut,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter()


@router.post("/prestadores", response_model=PrestadorOut, status_code=201)
async def create_prestador(
    body: PrestadorIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> PrestadorOut:
    prestador = await build_create_prestador(db).execute(
        nombre=body.nombre,
        nombre_corto=body.nombre_corto,
        cuit=body.cuit or None,
        region=body.region or None,
    )
    return PrestadorOut.from_entity(prestador)


@router.patch("/prestadores/{prestador_id}", response_model=PrestadorOut)
async def update_prestador(
    prestador_id: UUID,
    body: PrestadorIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> PrestadorOut:
    updated = await build_update_prestador(db).execute(
        prestador_id,
        nombre=body.nombre,
        nombre_corto=body.nombre_corto,
        cuit=body.cuit or None,
        region=body.region or None,
    )
    return PrestadorOut.from_entity(updated)


@router.patch("/prestadores/{prestador_id}/activo", response_model=PrestadorOut)
async def toggle_prestador_activo(
    prestador_id: UUID,
    body: ToggleActivoIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> PrestadorOut:
    updated = await build_toggle_prestador_activo(db).execute(prestador_id, activo=body.activo)
    return PrestadorOut.from_entity(updated)


@router.patch("/prestadores/{prestador_id}/base-sucursal", response_model=PrestadorOut)
async def vincular_base_sucursal_prestador(
    prestador_id: UUID,
    body: VincularBaseSucursalIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> PrestadorOut:
    updated = await SqlAlchemyPrestadorRepository(db).vincular_base_sucursal(
        prestador_id, siges_base_sucursal_id=body.siges_base_sucursal_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Prestador no encontrado")
    return PrestadorOut.from_entity(updated)


@router.patch("/prestadores/{prestador_id}/vincular-cd", response_model=PrestadorOut)
async def vincular_cd_prestador(
    prestador_id: UUID,
    body: VincularCdIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> PrestadorOut:
    updated = await SqlAlchemyPrestadorRepository(db).vincular_cd(
        prestador_id, cd_prestador_id=body.cd_prestador_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Prestador no encontrado")
    return PrestadorOut.from_entity(updated)


@router.delete("/prestadores/{prestador_id}", status_code=204)
async def delete_prestador(
    prestador_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    await build_delete_prestador(db).execute(prestador_id)


@router.get("/prestadores/export")
async def export_prestadores_csv(
    _: Identity = require_export,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    rows = await SqlAlchemyPrestadorRepository(db).list_all()
    return csv_export.export_prestadores(rows)


@router.post("/prestadores/import")
async def import_prestadores_csv(
    file: UploadFile = File(...),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    return await csv_helpers.import_prestadores(file, SqlAlchemyPrestadorRepository(db))


@router.post(
    "/prestadores/importar-excel", response_model=ImportarPrestadorMaestroOut, status_code=201
)
async def importar_excel_maestro(
    file: UploadFile = File(...),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> ImportarPrestadorMaestroOut:
    contenido = await file.read()
    resultado = await build_importar_prestador_maestro(db).execute(
        contenido=contenido, nombre_archivo=file.filename or ""
    )
    return ImportarPrestadorMaestroOut.from_dto(resultado)
