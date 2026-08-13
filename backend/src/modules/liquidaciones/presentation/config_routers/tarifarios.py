"""Endpoints de configuración de tarifarios (/api/liquidaciones/tarifarios).

El recadenado temporal de vigencias en alta/edición/baja vive en los casos de uso
(`application/use_cases/config_tarifarios.py`), no acá."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_repository import (  # noqa: E501
    SqlAlchemyTarifarioRepository,
)
from src.modules.liquidaciones.presentation import _liq_csv as csv_helpers
from src.modules.liquidaciones.presentation.config_routers._deps import (
    CATALOGO_SIZE,
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_create_tarifario,
    build_delete_tarifario,
    build_update_tarifario,
)
from src.modules.liquidaciones.presentation.schemas.config_schemas import (
    TarifarioIn,
    TarifarioOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


@router.get("/tarifarios", response_model=Page[TarifarioOut])
async def list_tarifarios(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=CATALOGO_SIZE, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[TarifarioOut]:
    repo = SqlAlchemyTarifarioRepository(db)
    rows = await (repo.list_by_prestador(prestador_id) if prestador_id else repo.list_all())
    return Page.of([TarifarioOut.from_entity(t) for t in rows], page=page, size=size)


@router.post("/tarifarios", response_model=TarifarioOut, status_code=201)
async def create_tarifario(
    body: TarifarioIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> TarifarioOut:
    tarifario = await build_create_tarifario(db).execute(
        prestador_id=body.prestador_id,
        tipo_servicio=body.tipo_servicio,
        zona=body.zona or None,
        costo_servicio=body.costo_servicio,
        costo_km=body.costo_km,
        vigencia_desde=body.vigencia_desde,
        vigencia_hasta=body.vigencia_hasta,
    )
    return TarifarioOut.from_entity(tarifario)


@router.patch("/tarifarios/{tarifario_id}", response_model=TarifarioOut)
async def update_tarifario(
    tarifario_id: UUID,
    body: TarifarioIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> TarifarioOut:
    updated = await build_update_tarifario(db).execute(
        tarifario_id,
        prestador_id=body.prestador_id,
        tipo_servicio=body.tipo_servicio,
        zona=body.zona or None,
        costo_servicio=body.costo_servicio,
        costo_km=body.costo_km,
        vigencia_desde=body.vigencia_desde,
        vigencia_hasta=body.vigencia_hasta,
    )
    return TarifarioOut.from_entity(updated)


@router.delete("/tarifarios/{tarifario_id}", status_code=204)
async def delete_tarifario(
    tarifario_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    await build_delete_tarifario(db).execute(tarifario_id)


@router.get("/tarifarios/export")
async def export_tarifarios_csv(
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    prestadores = await SqlAlchemyPrestadorRepository(db).list_all()
    pmap = {str(p.id): p.nombre_corto for p in prestadores}
    rows = await SqlAlchemyTarifarioRepository(db).list_all()
    return csv_helpers.export_tarifarios(rows, pmap)


@router.post("/tarifarios/import")
async def import_tarifarios_csv(
    file: UploadFile = File(...),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    return await csv_helpers.import_tarifarios(
        file, SqlAlchemyTarifarioRepository(db), SqlAlchemyPrestadorRepository(db)
    )
