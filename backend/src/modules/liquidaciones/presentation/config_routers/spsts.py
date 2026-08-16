"""Endpoints de configuración de SPSTs (/api/liquidaciones/spsts)."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.presentation import _liq_csv as csv_helpers
from src.modules.liquidaciones.presentation import _liq_csv_export as csv_export
from src.modules.liquidaciones.presentation.config_routers._deps import (
    CATALOGO_SIZE,
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_create_spst,
    build_delete_spst,
    build_toggle_spst_activo,
    build_update_spst,
)
from src.modules.liquidaciones.presentation.schemas.config_schemas import (
    SpstIn,
    SpstOut,
    ToggleActivoIn,
)
from src.modules.liquidaciones.presentation.schemas.siges_schemas import VincularBaseSucursalIn
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


@router.get("/spsts", response_model=Page[SpstOut])
async def list_spsts(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    solo_activos: bool = Query(default=False, alias="soloActivos"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=CATALOGO_SIZE, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[SpstOut]:
    rows = await SqlAlchemySpstRepository(db).list_all(
        prestador_id=prestador_id, solo_activos=solo_activos
    )
    return Page.of([SpstOut.from_entity(s) for s in rows], page=page, size=size)


@router.post("/spsts", response_model=SpstOut, status_code=201)
async def create_spst(
    body: SpstIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> SpstOut:
    spst = await build_create_spst(db).execute(
        prestador_id=body.prestador_id,
        nombre=body.nombre,
        domicilio=body.domicilio or None,
        localidad=body.localidad or None,
        provincia=body.provincia or None,
        zona=body.zona or None,
    )
    return SpstOut.from_entity(spst)


@router.patch("/spsts/{spst_id}", response_model=SpstOut)
async def update_spst(
    spst_id: UUID,
    body: SpstIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> SpstOut:
    updated = await build_update_spst(db).execute(
        spst_id,
        nombre=body.nombre,
        domicilio=body.domicilio or None,
        localidad=body.localidad or None,
        provincia=body.provincia or None,
        zona=body.zona or None,
    )
    return SpstOut.from_entity(updated)


@router.patch("/spsts/{spst_id}/activo", response_model=SpstOut)
async def toggle_spst_activo(
    spst_id: UUID,
    body: ToggleActivoIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> SpstOut:
    updated = await build_toggle_spst_activo(db).execute(spst_id, activo=body.activo)
    return SpstOut.from_entity(updated)


@router.put("/spsts/{spst_id}/siges-base-sucursal", response_model=SpstOut)
async def vincular_base_sucursal_spst(
    spst_id: UUID,
    body: VincularBaseSucursalIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> SpstOut:
    updated = await SqlAlchemySpstRepository(db).vincular_base_sucursal(
        spst_id, siges_base_sucursal_id=body.siges_base_sucursal_id
    )
    if updated is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    return SpstOut.from_entity(updated)


@router.delete("/spsts/{spst_id}", status_code=204)
async def delete_spst(
    spst_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    await build_delete_spst(db).execute(spst_id)


@router.get("/spsts/export")
async def export_spsts_csv(
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    prest_repo = SqlAlchemyPrestadorRepository(db)
    spst_repo = SqlAlchemySpstRepository(db)
    prestadores = await prest_repo.list_all()
    pmap = {str(p.id): p.nombre_corto for p in prestadores}
    return csv_export.export_spsts(await spst_repo.list_all(), pmap)


@router.post("/spsts/import")
async def import_spsts_csv(
    file: UploadFile = File(...),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    return await csv_helpers.import_spsts(
        file, SqlAlchemySpstRepository(db), SqlAlchemyPrestadorRepository(db)
    )
