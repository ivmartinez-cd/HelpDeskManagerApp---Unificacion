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
    build_proponer_vinculos_siges,
    build_sync_config_desde_siges,
    build_vincular_prestador_siges,
    build_vincular_spst_siges,
)
from src.modules.liquidaciones.presentation.schemas.config_schemas import (
    PrestadorOut,
    SpstOut,
)
from src.modules.liquidaciones.presentation.schemas.siges_schemas import (
    PropuestasVinculoOut,
    SyncSigesOut,
    VincularSigesIn,
)
from src.shared.infrastructure.database.session import get_db

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
