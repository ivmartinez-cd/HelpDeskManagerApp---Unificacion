"""Acciones sobre liquidaciones que hablan con wsAyC — sync masivo, backfill de
estado, aprobar/observar/anular (escritura), y la reconciliación puntual de una
sola liquidación al abrir su detalle.

Router propio (liquidaciones_router.py está al límite §4, mismo criterio que
alertas_router.py). Mismo prefijo/orden de registro: va ANTES del catch-all
GET/DELETE/PATCH /{liquidacion_id} de liquidaciones_router.py — acá no hay
ningún GET literal que ese catch-all pudiera interceptar, pero se mantiene el
mismo lugar en app.py por consistencia con alertas_router.py/config_router.py.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.liquidaciones.domain.well_known_permissions import APPROVE, CREATE, DELETE, VIEW
from src.modules.liquidaciones.presentation.dependencies import (
    build_anular_liquidacion,
    build_aprobar_liquidacion,
    build_backfill_estado,
    build_observar_liquidacion,
    build_recibir_liquidacion,
    build_reconciliar_liquidacion_individual,
    build_sincronizar_liquidaciones,
)
from src.modules.liquidaciones.presentation.schemas.backfill_schemas import BackfillEstadoOut
from src.modules.liquidaciones.presentation.schemas.liquidacion_schemas import LiquidacionOut
from src.modules.liquidaciones.presentation.schemas.sincronizar_schemas import SincronizarOut
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])

_require_view = Depends(require_permission(VIEW))
_require_create = Depends(require_permission(CREATE))
_require_approve = Depends(require_permission(APPROVE))
_require_delete = Depends(require_permission(DELETE))


@router.post("/sincronizar", response_model=SincronizarOut)
async def sincronizar_liquidaciones(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SincronizarOut:
    """Sin `prestadorId` sincroniza todos los prestadores vinculados; con él, solo
    ese (acota la corrida — el sync completo son miles de llamadas SOAP)."""
    resultado = await build_sincronizar_liquidaciones(db).execute(prestador_id)
    return SincronizarOut.from_dto(resultado)


@router.post("/backfill-estado", response_model=BackfillEstadoOut)
async def backfill_estado_liquidaciones(
    dry_run: bool = Query(default=True, alias="dryRun"),
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> BackfillEstadoOut:
    """Actualiza el `estado` de las liquidaciones `abierta` con su estado real en AyC.

    `?dryRun=true` (default) reporta sin escribir. Pasar `?dryRun=false` para ejecutar.
    Acotable con `?prestadorId=` (misma semántica que `/sincronizar`). Ver ADR-016.
    """
    resultado = await build_backfill_estado(db).execute(
        dry_run=dry_run, prestador_id=prestador_id
    )
    return BackfillEstadoOut.from_dto(resultado)


@router.post("/{liquidacion_id}/aprobar", response_model=LiquidacionOut)
async def aprobar_liquidacion(
    liquidacion_id: UUID,
    identity: Identity = _require_approve,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> LiquidacionOut:
    updated = await build_aprobar_liquidacion(db).execute(
        liquidacion_id, usuario=identity.user.full_name
    )
    return LiquidacionOut.from_entity(updated)


@router.post("/{liquidacion_id}/recibir", response_model=LiquidacionOut)
async def recibir_liquidacion(
    liquidacion_id: UUID,
    identity: Identity = _require_approve,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> LiquidacionOut:
    """Marca la liquidación como Recibida en AyC (paso previo a aprobar/observar)."""
    updated = await build_recibir_liquidacion(db).execute(
        liquidacion_id, usuario=identity.user.full_name
    )
    return LiquidacionOut.from_entity(updated)


@router.post("/{liquidacion_id}/observar", response_model=LiquidacionOut)
async def observar_liquidacion(
    liquidacion_id: UUID,
    identity: Identity = _require_approve,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> LiquidacionOut:
    updated = await build_observar_liquidacion(db).execute(
        liquidacion_id, usuario=identity.user.full_name
    )
    return LiquidacionOut.from_entity(updated)


@router.post("/{liquidacion_id}/anular", status_code=204)
async def anular_liquidacion(
    liquidacion_id: UUID,
    _: Identity = _require_delete,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    """Anula la liquidación en wsAyC (voidLiquidation) y la elimina localmente.
    Acción destructiva e irreversible desde nuestra app — el frontend pide confirmación
    explícita nombrando la liquidación antes de llamar a este endpoint."""
    await build_anular_liquidacion(db).execute(liquidacion_id)


@router.post("/{liquidacion_id}/reconciliar", status_code=204)
async def reconciliar_liquidacion(
    liquidacion_id: UUID,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    """Reconciliación best-effort de UNA liquidación contra AyC — se dispara al
    abrir su detalle. VIEW alcanza: es un refresh silencioso en segundo plano,
    no una acción explícita de escritura. Nunca falla por motivos esperados (sin
    vínculo AyC, estado terminal, SOAP caído) — ver
    `ReconciliarLiquidacionIndividual`. El caller vuelve a pedir el detalle
    (`GET /{liquidacion_id}`, en liquidaciones_router.py) para ver el resultado."""
    await build_reconciliar_liquidacion_individual(db).execute(liquidacion_id)
