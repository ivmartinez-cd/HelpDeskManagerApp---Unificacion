"""Acciones de geolocalización sobre filas de Tabla KM (búsqueda de lugar,
resolución de coordenadas, recálculo), separadas de `geolocalizacion.py`
porque ese archivo ya superaba el tamaño máximo (§4). A diferencia de ese
archivo (acciones a nivel prestador/Siges), estas operan sobre `tabla_km_id`.
Mismo prefijo `/api/liquidaciones` (montado por `config_router.py`)."""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.presentation.config_routers._deps import require_update
from src.modules.liquidaciones.presentation.dependencies import (
    build_buscar_lugar_fila,
    build_recalcular_km_fila,
    build_resolver_coordenadas_fila,
)
from src.modules.liquidaciones.presentation.schemas.config_schemas import TablaKmOut
from src.modules.liquidaciones.presentation.schemas.geolocalizacion_schemas import (
    GeocodeCandidatoOut,
    ResolverCoordenadasIn,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter()


class BuscarLugarOut(BaseModel):
    """Lista de candidatos, acotada por Google a <10 — objeto simple en vez de
    Page[T], mismo criterio que los reportes de sync (ADR-011)."""

    candidatos: list[GeocodeCandidatoOut]


@router.post("/tabla-km/{tabla_km_id}/buscar-lugar", response_model=BuscarLugarOut)
async def buscar_lugar_fila(
    tabla_km_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> BuscarLugarOut:
    candidatos = await build_buscar_lugar_fila(db).execute(tabla_km_id)
    return BuscarLugarOut(
        candidatos=[GeocodeCandidatoOut.from_entity(c) for c in candidatos]
    )


@router.put("/tabla-km/{tabla_km_id}/coordenadas", response_model=TablaKmOut)
async def resolver_coordenadas_fila(
    tabla_km_id: UUID,
    body: ResolverCoordenadasIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> TablaKmOut:
    fila = await build_resolver_coordenadas_fila(db).execute(
        tabla_km_id,
        candidato_idx=body.candidato_idx,
        latitud=body.latitud,
        longitud=body.longitud,
    )
    return TablaKmOut.from_entity(fila)


@router.post("/tabla-km/{tabla_km_id}/recalcular-km", response_model=TablaKmOut)
async def recalcular_km_fila(
    tabla_km_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> TablaKmOut:
    fila = await build_recalcular_km_fila(db).execute(tabla_km_id)
    return TablaKmOut.from_entity(fila)
