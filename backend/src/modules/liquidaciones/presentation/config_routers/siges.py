"""Endpoints de vínculo y sync de configuración contra Siges (ADR-014).

`/siges/propuestas` y `/siges/sync` devuelven reportes agregados (no listados
paginables — mismo criterio que ADR-011): el resultado es un objeto de sync con
listas internas acotadas por el tamaño del catálogo (~100 empresas)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.presentation.config_routers._deps import (
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_buscar_sucursales_siges,
    build_estado_zonas_siges,
    build_listar_sucursales_propias,
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
    db: AsyncSession = Depends(get_db),
) -> PropuestasVinculoOut:
    resultado = await build_proponer_vinculos_siges(db).execute()
    return PropuestasVinculoOut.from_dto(resultado)


@router.post("/siges/sync", response_model=SyncSigesOut)
async def sync_config_desde_siges(
    dry_run: bool = Query(default=True, alias="dryRun"),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> SyncSigesOut:
    resultado = await build_sync_config_desde_siges(db).execute(dry_run=dry_run)
    return SyncSigesOut.from_dto(resultado)


@router.get("/siges/zonas", response_model=ZonasSigesOut)
async def estado_zonas_siges(
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> ZonasSigesOut:
    resultado = await build_estado_zonas_siges(db).execute()
    return ZonasSigesOut.from_dto(resultado)


@router.put("/siges/zonas", response_model=ZonaMapOut)
async def mapear_zona_siges(
    body: MapearZonaIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> ZonaMapOut:
    mapa = await build_mapear_zona_siges(db).execute(
        body.prestador_id,
        descripcion_siges=body.descripcion_siges,
        zona_local=body.zona_local,
    )
    return ZonaMapOut.from_entity(mapa)


@router.post("/siges/sync-tarifarios", response_model=SyncTarifariosOut)
async def sync_tarifarios_desde_siges(
    dry_run: bool = Query(default=True, alias="dryRun"),
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> SyncTarifariosOut:
    resultado = await build_sync_tarifarios_desde_siges(db).execute(dry_run=dry_run)
    return SyncTarifariosOut.from_dto(resultado)


@router.get(
    "/siges/prestador/{prestador_id}/sucursales-propia",
    response_model=list[SucursalPropiaOut],
)
async def sucursales_propias_prestador(
    prestador_id: UUID,
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
) -> list[SucursalPropiaOut]:
    sucursales = await build_listar_sucursales_propias(db).execute(prestador_id)
    return [SucursalPropiaOut.from_entity(s) for s in sucursales]


@router.get("/siges/sucursales", response_model=Page[SucursalSigesOut])
async def buscar_sucursales_siges(
    prestador_id: UUID = Query(alias="prestadorId"),
    q: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
) -> PrestadorOut:
    actualizado = await build_vincular_prestador_siges(db).execute(
        prestador_id, siges_empresa_id=body.siges_empresa_id
    )
    return PrestadorOut.from_entity(actualizado)


@router.put("/spsts/{spst_id}/siges-vinculo", response_model=SpstOut)
async def vincular_spst_siges(
    spst_id: UUID,
    body: VincularSigesIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db),
) -> SpstOut:
    actualizado = await build_vincular_spst_siges(db).execute(
        spst_id, siges_empresa_id=body.siges_empresa_id
    )
    return SpstOut.from_entity(actualizado)
