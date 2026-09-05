"""Endpoints de geolocalización de Tabla KM a nivel prestador: estado del
asistente, cálculo de distancias en dos pasos (preview→apply), geocodificación
de sucursales sin pin, coordenadas y auditoría de pines sospechosos.

El pipeline de geovalidación (Tier 0/1/1b/worklist) vive en `geovalidacion.py`
y las acciones sobre filas de Tabla KM en `tabla_km_geo.py` — separados de
este archivo porque juntos superaban el tamaño máximo (§4)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
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
from src.modules.liquidaciones.presentation.config_routers._reanalisis import (
    reanalizar_abiertas,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_aplicar_calcular_distancias,
    build_auditar_pines,
    build_corregir_pin,
    build_diagnosticar_asistente_km,
    build_fijar_pin_manual,
    build_geocodificar_sucursales,
    build_listar_coordenadas_pendientes,
    build_listar_pines_sospechosos,
    build_preview_calcular_distancias,
    build_refrescar_datos_siges,
    build_resolver_coordenadas,
)
from src.modules.liquidaciones.presentation.schemas.asistente_km_schemas import (
    EstadoAsistenteKmOut,
)
from src.modules.liquidaciones.presentation.schemas.distancias_schemas import (
    AplicarDistanciasIn,
    AplicarDistanciasOut,
    CalculoKmPreviewOut,
)
from src.modules.liquidaciones.presentation.schemas.geolocalizacion_schemas import (
    AuditarPinesOut,
    GeocodificarResultadoOut,
    PinManualIn,
    PinSospechosoOut,
    RefrescarDireccionesOut,
    ResolverCoordenadasIn,
    SucursalCoordenadasOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


class AuditarPinesIn(BaseModel):
    """`sigesSucursalIds`, cuando se manda, acota la auditoría a ese
    subconjunto — el residuo real de Tier 2 (ver `geovalidacion/worklist`),
    en vez del prestador completo. `None`/vacío = comportamiento sin cambios."""

    model_config = ConfigDict(populate_by_name=True)
    siges_sucursal_ids: list[int] | None = Field(default=None, alias="sigesSucursalIds")


@router.get(
    "/siges/prestador/{prestador_id}/asistente-km/estado",
    response_model=EstadoAsistenteKmOut,
)
async def estado_asistente_km(
    prestador_id: UUID,
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
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
    db: AsyncSession = Depends(get_db, scope="function"),
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
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AplicarDistanciasOut:
    resultado = await build_aplicar_calcular_distancias(db).execute(
        body.preview_id, solo_sin_km=body.solo_sin_km
    )
    # Km nuevos en Tabla KM cambian lo que ALT002 espera: reanalizar las abiertas
    # igual que tras cualquier otro cambio de configuración.
    await reanalizar_abiertas(db, prestador_id)
    return AplicarDistanciasOut.from_resultado(resultado)


@router.post(
    "/siges/prestador/{prestador_id}/refrescar-datos-sucursales",
    response_model=RefrescarDireccionesOut,
)
async def refrescar_datos_sucursales(
    prestador_id: UUID,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
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
    db: AsyncSession = Depends(get_db, scope="function"),
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
    size: int = Query(default=100, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[SucursalCoordenadasOut]:
    filas = await build_listar_coordenadas_pendientes(db).execute(prestador_id)
    return Page.of([SucursalCoordenadasOut.from_dto(f) for f in filas], page=page, size=size)


@router.put(
    "/siges/prestador/{prestador_id}/coordenadas/{siges_sucursal_id}",
    response_model=SucursalCoordenadasOut,
)
async def resolver_coordenadas(
    prestador_id: UUID,
    siges_sucursal_id: int,
    body: ResolverCoordenadasIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SucursalCoordenadasOut:
    resuelta = await build_resolver_coordenadas(db).execute(
        siges_sucursal_id,
        candidato_idx=body.candidato_idx,
        latitud=body.latitud,
        longitud=body.longitud,
    )
    return SucursalCoordenadasOut.from_dto(SucursalConCandidatos(resuelta, ESTADO_RESUELTA, ()))


@router.get(
    "/siges/prestador/{prestador_id}/pines-sospechosos",
    response_model=Page[PinSospechosoOut],
)
async def listar_pines_sospechosos(
    prestador_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=100, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
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
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    await build_corregir_pin(db).execute(prestador_id, siges_sucursal_id)


@router.put(
    "/siges/prestador/{prestador_id}/sucursal/{siges_sucursal_id}/pin-manual",
    response_model=SucursalCoordenadasOut,
)
async def fijar_pin_manual(
    prestador_id: UUID,
    siges_sucursal_id: int,
    body: PinManualIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SucursalCoordenadasOut:
    """Coordenadas verificadas con evidencia para una sucursal, tenga o no pin
    en Gestión (override con procedencia `manual`; la fuente queda guardada)."""
    resuelta = await build_fijar_pin_manual(db).execute(
        prestador_id,
        siges_sucursal_id,
        latitud=body.latitud,
        longitud=body.longitud,
        fuente=body.fuente,
    )
    return SucursalCoordenadasOut.from_dto(SucursalConCandidatos(resuelta, ESTADO_RESUELTA, ()))


@router.post(
    "/siges/prestador/{prestador_id}/auditar-pines",
    response_model=AuditarPinesOut,
)
async def auditar_pines(
    prestador_id: UUID,
    body: AuditarPinesIn | None = None,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AuditarPinesOut:
    solo_ids = (
        frozenset(body.siges_sucursal_ids) if body is not None and body.siges_sucursal_ids else None
    )
    resultado = await build_auditar_pines(db).execute(prestador_id, solo_ids)
    return AuditarPinesOut.from_dto(resultado)
