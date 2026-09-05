"""Endpoints de vínculo y sync de configuración contra Siges (ADR-014).

`/siges/propuestas` y `/siges/sync` devuelven reportes agregados (no listados
paginables — mismo criterio que ADR-011): el resultado es un objeto de sync con
listas internas acotadas por el tamaño del catálogo (~100 empresas)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.presentation.config_routers._deps import (
    CATALOGO_SIZE,
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_buscar_sucursales_siges,
    build_eliminar_mapeo_cuadricula,
    build_estado_zonas_siges,
    build_listar_cuadriculas,
    build_listar_sucursales_propias,
    build_mapear_cuadricula,
    build_mapear_zona_siges,
    build_proponer_vinculos_siges,
    build_sync_config_desde_siges,
    build_sync_tarifarios_desde_siges,
    build_vincular_prestador_siges,
    build_vincular_spst_siges,
)
from src.modules.liquidaciones.presentation.schemas.config_schemas import (
    PrestadorOut,
    SpstOut,
)
from src.modules.liquidaciones.presentation.schemas.cuadricula_schemas import (
    CuadriculaMapOut,
    CuadriculaOut,
    MapearCuadriculaIn,
)
from src.modules.liquidaciones.presentation.schemas.distancias_schemas import (
    SucursalPropiaOut,
)
from src.modules.liquidaciones.presentation.schemas.siges_schemas import (
    MapearZonaIn,
    PropuestasVinculoOut,
    SucursalSigesOut,
    SyncSigesOut,
    SyncTarifariosOut,
    VincularSigesIn,
    ZonaMapOut,
    ZonasSigesOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


@router.get("/siges/propuestas", response_model=PropuestasVinculoOut)
async def propuestas_vinculo_siges(
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> PropuestasVinculoOut:
    resultado = await build_proponer_vinculos_siges(db).execute()
    return PropuestasVinculoOut.from_dto(resultado)


@router.post("/siges/sync", response_model=SyncSigesOut)
async def sync_config_desde_siges(
    dry_run: bool = Query(default=True, alias="dryRun"),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SyncSigesOut:
    resultado = await build_sync_config_desde_siges(db).execute(dry_run=dry_run)
    return SyncSigesOut.from_dto(resultado)


@router.get("/siges/zonas", response_model=ZonasSigesOut)
async def estado_zonas_siges(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ZonasSigesOut:
    resultado = await build_estado_zonas_siges(db).execute(prestador_id)
    return ZonasSigesOut.from_dto(resultado)


@router.put("/siges/zonas", response_model=ZonaMapOut)
async def mapear_zona_siges(
    body: MapearZonaIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ZonaMapOut:
    mapa = await build_mapear_zona_siges(db).execute(
        body.prestador_id,
        descripcion_siges=body.descripcion_siges,
        spst_id=body.spst_id,
    )
    return ZonaMapOut.from_entity(mapa)


@router.post("/siges/sync-tarifarios", response_model=SyncTarifariosOut)
async def sync_tarifarios_desde_siges(
    dry_run: bool = Query(default=True, alias="dryRun"),
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SyncTarifariosOut:
    resultado = await build_sync_tarifarios_desde_siges(db).execute(
        dry_run=dry_run, prestador_id=prestador_id
    )
    return SyncTarifariosOut.from_dto(resultado)


@router.get(
    "/siges/prestador/{prestador_id}/sucursales-propia",
    response_model=Page[SucursalPropiaOut],
)
async def sucursales_propias_prestador(
    prestador_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=CATALOGO_SIZE, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[SucursalPropiaOut]:
    sucursales = await build_listar_sucursales_propias(db).execute(prestador_id)
    return Page.of(
        [SucursalPropiaOut.from_entity(s) for s in sucursales], page=page, size=size
    )


@router.get("/siges/sucursales", response_model=Page[SucursalSigesOut])
async def buscar_sucursales_siges(
    prestador_id: UUID = Query(alias="prestadorId"),
    q: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[SucursalSigesOut]:
    sucursales = await build_buscar_sucursales_siges(db).execute(prestador_id, q=q)
    return Page.of(
        [SucursalSigesOut.from_dto(s) for s in sucursales], page=page, size=size
    )


@router.put("/prestadores/{prestador_id}/siges-vinculo", response_model=PrestadorOut)
async def vincular_prestador_siges(
    prestador_id: UUID,
    body: VincularSigesIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> PrestadorOut:
    actualizado = await build_vincular_prestador_siges(db).execute(
        prestador_id, siges_empresa_id=body.siges_empresa_id
    )
    return PrestadorOut.from_entity(actualizado)


@router.get(
    "/siges/prestador/{prestador_id}/cuadriculas",
    response_model=Page[CuadriculaOut],
)
async def listar_cuadriculas(
    prestador_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=CATALOGO_SIZE, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[CuadriculaOut]:
    resultado = await build_listar_cuadriculas(db).execute(prestador_id)
    return Page.of([CuadriculaOut.from_dto(c) for c in resultado], page=page, size=size)


@router.put(
    "/siges/prestador/{prestador_id}/cuadriculas/{cuadricula}",
    response_model=CuadriculaMapOut,
)
async def mapear_cuadricula(
    prestador_id: UUID,
    cuadricula: str,
    body: MapearCuadriculaIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> CuadriculaMapOut:
    resultado = await build_mapear_cuadricula(db).execute(
        prestador_id, cuadricula=cuadricula,
        siges_base_sucursal_id=body.siges_base_sucursal_id,
    )
    return CuadriculaMapOut.from_entity(resultado)


@router.delete(
    "/siges/prestador/{prestador_id}/cuadriculas/{cuadricula}",
    status_code=204,
)
async def eliminar_mapeo_cuadricula(
    prestador_id: UUID,
    cuadricula: str,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    await build_eliminar_mapeo_cuadricula(db).execute(prestador_id, cuadricula=cuadricula)


@router.put("/spsts/{spst_id}/siges-vinculo", response_model=SpstOut)
async def vincular_spst_siges(
    spst_id: UUID,
    body: VincularSigesIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SpstOut:
    actualizado = await build_vincular_spst_siges(db).execute(
        spst_id, siges_empresa_id=body.siges_empresa_id
    )
    return SpstOut.from_entity(actualizado)
