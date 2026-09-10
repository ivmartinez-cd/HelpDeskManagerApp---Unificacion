"""Modificaciones del prestador sobre una liquidación ya importada — ADR-038.

Repo directo (mismo criterio que otros endpoints de solo lectura de
`liquidaciones_router.py`, ver su docstring): no hay lógica de dominio más
allá de paginar/filtrar/enriquecer con el número de liquidación, no amerita
un use case. Router propio porque `liquidaciones_router.py` está al límite
de tamaño (§4)."""

from collections.abc import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.liquidaciones.domain.entities.modificacion_prestador import (
    ModificacionPrestador,
)
from src.modules.liquidaciones.domain.well_known_permissions import UPDATE, VIEW
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_modificacion_prestador_repository import (  # noqa: E501
    SqlAlchemyModificacionPrestadorRepository,
)
from src.modules.liquidaciones.presentation.schemas.modificacion_schemas import (
    MarcarVistasOut,
    ModificacionOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))


@router.get("/modificaciones", response_model=Page[ModificacionOut])
async def list_modificaciones_no_vistas(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=1000),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[ModificacionOut]:
    """No vistas de todas las liquidaciones — el frontend usa `total` para el
    badge del menú y arma un toast por liquidación con los items."""
    filas = await SqlAlchemyModificacionPrestadorRepository(db).list_no_vistas()
    items = await _a_schema(db, filas)
    return Page.of(items, page=page, size=size)


@router.get("/{liquidacion_id}/modificaciones", response_model=Page[ModificacionOut])
async def list_modificaciones_liquidacion(
    liquidacion_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=1000),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[ModificacionOut]:
    filas = await SqlAlchemyModificacionPrestadorRepository(db).list_by_liquidacion(
        liquidacion_id
    )
    items = await _a_schema(db, filas)
    return Page.of(items, page=page, size=size)


@router.post("/{liquidacion_id}/modificaciones/marcar-vistas", response_model=MarcarVistasOut)
async def marcar_vistas(
    liquidacion_id: UUID,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> MarcarVistasOut:
    actualizadas = await SqlAlchemyModificacionPrestadorRepository(db).marcar_vistas(
        liquidacion_id
    )
    return MarcarVistasOut(actualizadas=actualizadas)


async def _a_schema(
    db: AsyncSession, filas: Sequence[ModificacionPrestador]
) -> list[ModificacionOut]:
    numeros = await _numeros_liquidacion(db, {f.liquidacion_id for f in filas})
    return [
        ModificacionOut.from_entity(f, numero_liquidacion=numeros.get(f.liquidacion_id))
        for f in filas
    ]


async def _numeros_liquidacion(
    db: AsyncSession, liquidacion_ids: set[UUID]
) -> dict[UUID, str | None]:
    liquidaciones = SqlAlchemyLiquidacionRepository(db)
    resultado: dict[UUID, str | None] = {}
    for liquidacion_id in liquidacion_ids:
        liq = await liquidaciones.get_by_id(liquidacion_id)
        resultado[liquidacion_id] = liq.numero_liquidacion if liq else None
    return resultado
