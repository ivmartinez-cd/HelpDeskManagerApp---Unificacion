"""Endpoints de configuración de tabla KM (/api/liquidaciones/tabla-km)."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (  # noqa: E501
    SqlAlchemyTablaKmRepository,
)
from src.modules.liquidaciones.presentation import _liq_csv as csv_helpers
from src.modules.liquidaciones.presentation.config_routers._deps import (
    CATALOGO_SIZE,
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.schemas.config_schemas import (
    TablaKmIn,
    TablaKmOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


@router.get("/tabla-km", response_model=Page[TablaKmOut])
async def list_tabla_km(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=CATALOGO_SIZE, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[TablaKmOut]:
    rows = await SqlAlchemyTablaKmRepository(db).list_all(prestador_id=prestador_id, q=q)
    return Page.of([TablaKmOut.from_entity(t) for t in rows], page=page, size=size)


@router.post("/tabla-km", response_model=TablaKmOut, status_code=201)
async def create_tabla_km(
    body: TablaKmIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> TablaKmOut:
    row = await SqlAlchemyTablaKmRepository(db).create(
        prestador_id=body.prestador_id,
        spst_id=body.spst_id,
        empresa_nombre=body.empresa_nombre,
        sucursal_nombre=body.sucursal_nombre,
        observaciones=body.observaciones,
        domicilio_cliente=body.domicilio_cliente,
        localidad_cliente=body.localidad_cliente,
        provincia_cliente=body.provincia_cliente,
        kms_recorrido=body.kms_recorrido,
        umbral_viatico=body.umbral_viatico,
        aplica_viatico=body.aplica_viatico,
        kms_a_facturar=body.kms_a_facturar,
        url_maps=body.url_maps,
    )
    return TablaKmOut.from_entity(row)


@router.patch("/tabla-km/{tabla_km_id}", response_model=TablaKmOut)
async def update_tabla_km(
    tabla_km_id: UUID,
    body: TablaKmIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> TablaKmOut:
    updated = await SqlAlchemyTablaKmRepository(db).update(
        tabla_km_id,
        prestador_id=body.prestador_id,
        spst_id=body.spst_id,
        empresa_nombre=body.empresa_nombre,
        sucursal_nombre=body.sucursal_nombre,
        observaciones=body.observaciones,
        domicilio_cliente=body.domicilio_cliente,
        localidad_cliente=body.localidad_cliente,
        provincia_cliente=body.provincia_cliente,
        kms_recorrido=body.kms_recorrido,
        umbral_viatico=body.umbral_viatico,
        aplica_viatico=body.aplica_viatico,
        kms_a_facturar=body.kms_a_facturar,
        url_maps=body.url_maps,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Entrada de Tabla KM no encontrada")
    return TablaKmOut.from_entity(updated)


@router.delete("/tabla-km/{tabla_km_id}", status_code=204)
async def delete_tabla_km(
    tabla_km_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await SqlAlchemyTablaKmRepository(db).delete(tabla_km_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entrada de Tabla KM no encontrada")


@router.get("/tabla-km/export")
async def export_tabla_km_csv(
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    prestadores = await SqlAlchemyPrestadorRepository(db).list_all()
    pmap = {str(p.id): p.nombre_corto for p in prestadores}
    rows = await SqlAlchemyTablaKmRepository(db).list_all()
    return csv_helpers.export_tabla_km(rows, pmap)


@router.post("/tabla-km/import")
async def import_tabla_km_csv(
    file: UploadFile = File(...),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    return await csv_helpers.import_tabla_km(
        file, SqlAlchemyTablaKmRepository(db), SqlAlchemyPrestadorRepository(db)
    )
