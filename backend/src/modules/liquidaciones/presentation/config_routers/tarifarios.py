"""Endpoints de configuración de tarifarios (/api/liquidaciones/tarifarios).

Todo alta/edición/baja recalcula la cadena temporal de vigencias del grupo
(prestador, tipo_servicio, zona) afectado — ver
`domain/services/cadena_tarifaria.py` (port de `_rebuild_temporal_chain` legacy)."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.services.cadena_tarifaria import recalcular_cadena
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
from src.modules.liquidaciones.presentation.schemas.config_schemas import (
    TarifarioIn,
    TarifarioOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


async def _recadenar_grupo(
    repo: SqlAlchemyTarifarioRepository,
    *,
    prestador_id: UUID,
    tipo_servicio: str,
    zona: str | None,
) -> None:
    grupo = await repo.list_grupo(
        prestador_id=prestador_id, tipo_servicio=tipo_servicio, zona=zona
    )
    for ajuste in recalcular_cadena(grupo):
        await repo.set_vigencia_hasta(ajuste.tarifario_id, ajuste.vigencia_hasta)


async def _recadenar_para(repo: SqlAlchemyTarifarioRepository, t: Tarifario) -> None:
    await _recadenar_grupo(
        repo, prestador_id=t.prestador_id, tipo_servicio=t.tipo_servicio, zona=t.zona
    )


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
    repo = SqlAlchemyTarifarioRepository(db)
    tarifario = await repo.create(
        prestador_id=body.prestador_id,
        tipo_servicio=body.tipo_servicio,
        zona=body.zona or None,
        costo_servicio=body.costo_servicio,
        costo_km=body.costo_km,
        vigencia_desde=body.vigencia_desde,
        vigencia_hasta=body.vigencia_hasta,
    )
    await _recadenar_para(repo, tarifario)
    refrescado = await repo.get_by_id(tarifario.id)
    return TarifarioOut.from_entity(refrescado or tarifario)


@router.patch("/tarifarios/{tarifario_id}", response_model=TarifarioOut)
async def update_tarifario(
    tarifario_id: UUID,
    body: TarifarioIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> TarifarioOut:
    repo = SqlAlchemyTarifarioRepository(db)
    anterior = await repo.get_by_id(tarifario_id)
    if anterior is None:
        raise HTTPException(status_code=404, detail="Tarifario no encontrado")
    updated = await repo.update(
        tarifario_id,
        prestador_id=body.prestador_id,
        tipo_servicio=body.tipo_servicio,
        zona=body.zona or None,
        costo_servicio=body.costo_servicio,
        costo_km=body.costo_km,
        vigencia_desde=body.vigencia_desde,
        vigencia_hasta=body.vigencia_hasta,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Tarifario no encontrado")
    await _recadenar_para(repo, anterior)
    if (updated.prestador_id, updated.tipo_servicio, updated.zona) != (
        anterior.prestador_id,
        anterior.tipo_servicio,
        anterior.zona,
    ):
        await _recadenar_para(repo, updated)
    refrescado = await repo.get_by_id(tarifario_id)
    return TarifarioOut.from_entity(refrescado or updated)


@router.delete("/tarifarios/{tarifario_id}", status_code=204)
async def delete_tarifario(
    tarifario_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    repo = SqlAlchemyTarifarioRepository(db)
    anterior = await repo.get_by_id(tarifario_id)
    if anterior is None or not await repo.delete(tarifario_id):
        raise HTTPException(status_code=404, detail="Tarifario no encontrado")
    await _recadenar_para(repo, anterior)


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
