"""Bitácora de Web Agentes de una liquidación (comentarios de PST y de Canal
Directo), de solo lectura. Router propio porque `liquidaciones_router.py`
está al límite de tamaño (§4)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.liquidaciones.application.use_cases.listar_bitacora_liquidacion import (
    ListarBitacoraLiquidacion,
)
from src.modules.liquidaciones.domain.well_known_permissions import VIEW
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.siges.pyodbc_bitacora_gateway import (
    PyodbcBitacoraGateway,
)
from src.modules.liquidaciones.presentation.schemas.bitacora_schemas import EntradaBitacoraOut
from src.shared.infrastructure.database.session import get_db
from src.shared.infrastructure.orion.factories import require_orion_runner
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])

_require_view = Depends(require_permission(VIEW))


@router.get("/{liquidacion_id}/bitacora", response_model=Page[EntradaBitacoraOut])
async def list_bitacora_liquidacion(
    liquidacion_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=200, ge=1, le=1000),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[EntradaBitacoraOut]:
    caso = ListarBitacoraLiquidacion(
        SqlAlchemyLiquidacionRepository(db), PyodbcBitacoraGateway(require_orion_runner())
    )
    entradas = await caso.execute(liquidacion_id)
    items = [EntradaBitacoraOut.from_entity(e) for e in entradas]
    return Page.of(items, page=page, size=size)
