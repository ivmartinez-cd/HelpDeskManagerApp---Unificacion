"""Endpoints de liquidaciones — listado, importación, detalle y reanálisis.

Orden de registro importa: `/prestadores` e `/importar` van ANTES de `/{liquidacion_id}`
para que FastAPI no intente parsear esos segmentos como UUID y devuelva 422."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.liquidaciones.domain.well_known_permissions import (
    APPROVE,
    CREATE,
    DELETE,
    UPDATE,
    VIEW,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_observacion_repository import (  # noqa: E501
    SqlAlchemyObservacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_anular_liquidacion,
    build_aprobar_liquidacion,
    build_backfill_estado,
    build_get_liquidacion_detalle,
    build_importar_liquidacion,
    build_list_liquidaciones,
    build_observar_liquidacion,
    build_reanalizar_liquidacion,
    build_sincronizar_liquidaciones,
)
from src.modules.liquidaciones.presentation.schemas.backfill_schemas import BackfillEstadoOut
from src.modules.liquidaciones.presentation.schemas.importar_liquidacion_schemas import (
    ImportarLiquidacionOut,
)
from src.modules.liquidaciones.presentation.schemas.liquidacion_detalle_schemas import (
    LiquidacionDetalleOut,
    ObservacionEstadoIn,
    ObservacionOut,
)
from src.modules.liquidaciones.presentation.schemas.liquidacion_schemas import (
    EstadoIn,
    ExtraIn,
    LiquidacionOut,
    PrestadorLiquidacionOut,
    ResumenLiquidacionesOut,
)
from src.modules.liquidaciones.presentation.schemas.reanalizar_liquidacion_schemas import (
    ReanalizarLiquidacionOut,
)
from src.modules.liquidaciones.presentation.schemas.sincronizar_schemas import SincronizarOut
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_require_create = Depends(require_permission(CREATE))
_require_approve = Depends(require_permission(APPROVE))
_require_delete = Depends(require_permission(DELETE))
# Catálogo chico que alimenta combos y el listado completo de config — el
# contrato sigue paginado con default generoso (mismo criterio que prestadores).
_CATALOGO_SIZE = 500


@router.get("/prestadores", response_model=Page[PrestadorLiquidacionOut])
async def list_prestadores(
    solo_activos: bool = Query(default=True, alias="soloActivos"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_CATALOGO_SIZE, ge=1, le=1000),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[PrestadorLiquidacionOut]:
    rows = await SqlAlchemyPrestadorRepository(db).list_all(solo_activos=solo_activos)
    return Page.of(
        [PrestadorLiquidacionOut.from_entity(p) for p in rows], page=page, size=size
    )


@router.get("", response_model=Page[LiquidacionOut])
async def list_liquidaciones(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    estado: str | None = Query(default=None),
    periodo: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=1000),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[LiquidacionOut]:
    liquidaciones = await build_list_liquidaciones(db).execute(
        prestador_id=prestador_id, estado=estado, periodo=periodo
    )
    return Page.of(
        [LiquidacionOut.from_entity(item) for item in liquidaciones], page=page, size=size
    )


@router.get("/periodos", response_model=Page[str])
async def list_periodos(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_CATALOGO_SIZE, ge=1, le=1000),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[str]:
    """Valores distintos de período (YYYY-MM) para poblar el dropdown de filtros."""
    periodos = await SqlAlchemyLiquidacionRepository(db).list_periodos()
    return Page.of(periodos, page=page, size=size)


@router.post("/importar", response_model=ImportarLiquidacionOut, status_code=201)
async def importar_liquidacion(
    file: UploadFile = File(...),
    prestador_id: UUID = Form(alias="prestadorId"),
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db),
) -> ImportarLiquidacionOut:
    contenido = await file.read()
    resultado = await build_importar_liquidacion(db).execute(
        prestador_id=prestador_id, contenido=contenido, nombre_archivo=file.filename or ""
    )
    return ImportarLiquidacionOut.from_dto(resultado)


@router.post("/sincronizar", response_model=SincronizarOut)
async def sincronizar_liquidaciones(
    prestador_id: UUID | None = Query(default=None, alias="prestadorId"),
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
) -> BackfillEstadoOut:
    """Actualiza el `estado` de las liquidaciones `abierta` con su estado real en AyC.

    `?dryRun=true` (default) reporta sin escribir. Pasar `?dryRun=false` para ejecutar.
    Acotable con `?prestadorId=` (misma semántica que `/sincronizar`). Ver ADR-016.
    """
    resultado = await build_backfill_estado(db).execute(
        dry_run=dry_run, prestador_id=prestador_id
    )
    return BackfillEstadoOut.from_dto(resultado)


@router.get("/resumen", response_model=ResumenLiquidacionesOut)
async def get_resumen_liquidaciones(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> ResumenLiquidacionesOut:
    """Conteo de liquidaciones pendientes de aprobación (abierta/preliquidada/recibida/observada)."""
    count = await SqlAlchemyLiquidacionRepository(db).count_pendientes()
    return ResumenLiquidacionesOut(pendientes=count)


@router.patch("/{liquidacion_id}/estado", response_model=LiquidacionOut)
async def update_estado_liquidacion(
    liquidacion_id: UUID,
    body: EstadoIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> LiquidacionOut:
    updated = await SqlAlchemyLiquidacionRepository(db).update_estado(
        liquidacion_id, body.estado
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    return LiquidacionOut.from_entity(updated)


@router.patch("/{liquidacion_id}/extra", response_model=LiquidacionOut)
async def update_extra_liquidacion(
    liquidacion_id: UUID,
    body: ExtraIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> LiquidacionOut:
    updated = await SqlAlchemyLiquidacionRepository(db).update_extra(
        liquidacion_id, body.concepto_extra, body.monto_extra
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    return LiquidacionOut.from_entity(updated)


@router.patch(
    "/{liquidacion_id}/observaciones/{observacion_id}/estado",
    response_model=ObservacionOut,
)
async def update_estado_observacion(
    liquidacion_id: UUID,
    observacion_id: UUID,
    body: ObservacionEstadoIn,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> ObservacionOut:
    updated = await SqlAlchemyObservacionRepository(db).update_estado(
        liquidacion_id, observacion_id, body.estado
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
    return ObservacionOut.from_entity(updated)


@router.post("/{liquidacion_id}/aprobar", response_model=LiquidacionOut)
async def aprobar_liquidacion(
    liquidacion_id: UUID,
    identity: Identity = _require_approve,
    db: AsyncSession = Depends(get_db),
) -> LiquidacionOut:
    updated = await build_aprobar_liquidacion(db).execute(
        liquidacion_id, usuario=identity.user.full_name
    )
    return LiquidacionOut.from_entity(updated)


@router.post("/{liquidacion_id}/observar", response_model=LiquidacionOut)
async def observar_liquidacion(
    liquidacion_id: UUID,
    identity: Identity = _require_approve,
    db: AsyncSession = Depends(get_db),
) -> LiquidacionOut:
    updated = await build_observar_liquidacion(db).execute(
        liquidacion_id, usuario=identity.user.full_name
    )
    return LiquidacionOut.from_entity(updated)


@router.post("/{liquidacion_id}/anular", status_code=204)
async def anular_liquidacion(
    liquidacion_id: UUID,
    _: Identity = _require_delete,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Anula la liquidación en wsAyC (voidLiquidation) y la elimina localmente.
    Acción destructiva e irreversible desde nuestra app — el frontend pide confirmación
    explícita nombrando la liquidación antes de llamar a este endpoint."""
    await build_anular_liquidacion(db).execute(liquidacion_id)


@router.delete("/{liquidacion_id}", status_code=204)
async def delete_liquidacion(
    liquidacion_id: UUID,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    # Baja local únicamente — para liquidaciones sin numero_liquidacion (CSV sin AyC ID).
    # Para liquidaciones con vínculo AyC, usar POST /{id}/anular.
    deleted = await SqlAlchemyLiquidacionRepository(db).delete(liquidacion_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")


@router.get("/{liquidacion_id}", response_model=LiquidacionDetalleOut)
async def get_liquidacion_detalle(
    liquidacion_id: UUID,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> LiquidacionDetalleOut:
    detalle = await build_get_liquidacion_detalle(db).execute(liquidacion_id)
    return LiquidacionDetalleOut.from_dto(detalle)


@router.post("/{liquidacion_id}/reanalyze", response_model=ReanalizarLiquidacionOut)
async def reanalyze_liquidacion(
    liquidacion_id: UUID,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> ReanalizarLiquidacionOut:
    resultado = await build_reanalizar_liquidacion(db).execute(liquidacion_id)
    return ReanalizarLiquidacionOut.from_dto(resultado)
