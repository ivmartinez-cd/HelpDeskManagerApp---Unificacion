"""Endpoints de geolocalización de Tabla KM: cálculo de distancias en dos
pasos (preview→apply), geocodificación de sucursales sin pin, resolución de
coordenadas y auditoría de pines sospechosos.

`buscar-lugar` devuelve un objeto con la lista de candidatos (acotada por
Google a <10) en vez de Page[T] — mismo criterio que los reportes de sync
(ADR-011). Los listados reales (coordenadas, pines) sí van paginados."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.application.use_cases.resolver_coordenadas import (
    ESTADO_RESUELTA,
    SucursalConCandidatos,
)
from src.modules.liquidaciones.presentation.config_routers._deps import (
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_aplicar_calcular_distancias,
    build_auditar_pines,
    build_buscar_lugar_fila,
    build_corregir_pin,
    build_diagnosticar_asistente_km,
    build_geocodificar_sucursales,
    build_listar_coordenadas_pendientes,
    build_listar_pines_sospechosos,
    build_preview_calcular_distancias,
    build_recalcular_km_fila,
    build_refrescar_datos_siges,
    build_resolver_coordenadas,
    build_resolver_coordenadas_fila,
)
from src.modules.liquidaciones.presentation.schemas.asistente_km_schemas import (
    EstadoAsistenteKmOut,
)
from src.modules.liquidaciones.presentation.schemas.config_schemas import TablaKmOut
from src.modules.liquidaciones.presentation.schemas.distancias_schemas import (
    AplicarDistanciasIn,
    AplicarDistanciasOut,
    CalculoKmPreviewOut,
)
from src.modules.liquidaciones.presentation.schemas.geolocalizacion_schemas import (
    AuditarPinesOut,
    GeocodeCandidatoOut,
    GeocodificarResultadoOut,
    PinSospechosoOut,
    RefrescarDireccionesOut,
    ResolverCoordenadasIn,
    SucursalCoordenadasOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


class BuscarLugarOut(BaseModel):
    candidatos: list[GeocodeCandidatoOut]


@router.get(
    "/siges/prestador/{prestador_id}/asistente-km/estado",
    response_model=EstadoAsistenteKmOut,
)
async def estado_asistente_km(
    prestador_id: UUID,
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> EstadoAsistenteKmOut:
    """Diagnóstico read-only del wizard: qué falta y cuánto costaría cada
    acción en llamadas Google — sin consumir ninguna."""
    estado = await build_diagnosticar_asistente_km(db).execute(prestador_id)
    return EstadoAsistenteKmOut.from_dto(estado)


@router.post(
    "/siges/prestador/{prestador_id}/calcular-distancias/preview",
    response_model=CalculoKmPreviewOut,
)
async def preview_calcular_distancias(
    prestador_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> CalculoKmPreviewOut:
    preview = await build_preview_calcular_distancias(db).execute(prestador_id)
    return CalculoKmPreviewOut.from_entity(preview)


@router.post(
    "/siges/prestador/{prestador_id}/calcular-distancias/aplicar",
    response_model=AplicarDistanciasOut,
)
async def aplicar_calcular_distancias(
    prestador_id: UUID,
    body: AplicarDistanciasIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> AplicarDistanciasOut:
    resultado = await build_aplicar_calcular_distancias(db).execute(body.preview_id)
    return AplicarDistanciasOut.from_resultado(resultado)


@router.post(
    "/siges/prestador/{prestador_id}/refrescar-datos-sucursales",
    response_model=RefrescarDireccionesOut,
)
async def refrescar_datos_sucursales(
    prestador_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> RefrescarDireccionesOut:
    resultado = await build_refrescar_datos_siges(db).execute(prestador_id)
    return RefrescarDireccionesOut.from_dto(resultado)


@router.post(
    "/siges/prestador/{prestador_id}/geocodificar-faltantes",
    response_model=GeocodificarResultadoOut,
)
async def geocodificar_faltantes(
    prestador_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> GeocodificarResultadoOut:
    resultado = await build_geocodificar_sucursales(db).execute(prestador_id)
    return GeocodificarResultadoOut.from_dto(resultado)


@router.get(
    "/siges/prestador/{prestador_id}/coordenadas",
    response_model=Page[SucursalCoordenadasOut],
)
async def listar_coordenadas(
    prestador_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=100, ge=1, le=500),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[SucursalCoordenadasOut]:
    filas = await build_listar_coordenadas_pendientes(db).execute(prestador_id)
    return Page.of(
        [SucursalCoordenadasOut.from_dto(f) for f in filas], page=page, size=size
    )


@router.put(
    "/siges/prestador/{prestador_id}/coordenadas/{siges_sucursal_id}",
    response_model=SucursalCoordenadasOut,
)
async def resolver_coordenadas(
    prestador_id: UUID,
    siges_sucursal_id: int,
    body: ResolverCoordenadasIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> SucursalCoordenadasOut:
    resuelta = await build_resolver_coordenadas(db).execute(
        siges_sucursal_id,
        candidato_idx=body.candidato_idx,
        latitud=body.latitud,
        longitud=body.longitud,
    )
    return SucursalCoordenadasOut.from_dto(
        SucursalConCandidatos(resuelta, ESTADO_RESUELTA, ())
    )


@router.get(
    "/siges/prestador/{prestador_id}/pines-sospechosos",
    response_model=Page[PinSospechosoOut],
)
async def listar_pines_sospechosos(
    prestador_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=100, ge=1, le=500),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[PinSospechosoOut]:
    pines = await build_listar_pines_sospechosos(db).execute(prestador_id)
    return Page.of([PinSospechosoOut.from_dto(p) for p in pines], page=page, size=size)


@router.post(
    "/siges/prestador/{prestador_id}/sucursal/{siges_sucursal_id}/corregir-pin",
    status_code=204,
)
async def corregir_pin(
    prestador_id: UUID,
    siges_sucursal_id: int,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    await build_corregir_pin(db).execute(prestador_id, siges_sucursal_id)


@router.post(
    "/siges/prestador/{prestador_id}/auditar-pines",
    response_model=AuditarPinesOut,
)
async def auditar_pines(
    prestador_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> AuditarPinesOut:
    resultado = await build_auditar_pines(db).execute(prestador_id)
    return AuditarPinesOut.from_dto(resultado)


@router.post("/tabla-km/{tabla_km_id}/buscar-lugar", response_model=BuscarLugarOut)
async def buscar_lugar_fila(
    tabla_km_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
) -> TablaKmOut:
    fila = await build_recalcular_km_fila(db).execute(tabla_km_id)
    return TablaKmOut.from_entity(fila)
