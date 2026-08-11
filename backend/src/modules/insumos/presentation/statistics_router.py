"""Endpoints de estadísticas históricas (agregación en vivo sobre order_audit).

Ninguno de los dos devuelve una colección: son un resumen con rankings acotados
adentro, por eso no van envueltos en Page[T] (ARCHITECTURE_GUIDE §11).
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.domain.well_known_permissions import VIEW
from src.modules.insumos.presentation.dependencies import (
    build_get_customer_statistics,
    build_get_statistics_overview,
)
from src.modules.insumos.presentation.schemas.customer_statistics_schemas import (
    CustomerDetailResponse,
)
from src.modules.insumos.presentation.schemas.statistics_schemas import (
    EstadisticasResponse,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))
_days = Query(default=None, gt=0, description="Últimos N días; ignorado si hay startDate")
_start = Query(default=None, alias="startDate")
_end = Query(default=None, alias="endDate")


@router.get("/estadisticas", response_model=EstadisticasResponse)
async def get_estadisticas(
    days: int | None = _days,
    start_date: date | None = _start,
    end_date: date | None = _end,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> EstadisticasResponse:
    """Tendencia diaria de pedidos y rankings de clientes/SKUs, con comparativa contra
    el período inmediatamente anterior del mismo largo."""
    result = await build_get_statistics_overview(db).execute(days, start_date, end_date)
    return EstadisticasResponse.from_result(result)


@router.get("/estadisticas/clientes/{customer_id}", response_model=CustomerDetailResponse)
async def get_estadisticas_cliente(
    customer_id: int,
    days: int | None = _days,
    start_date: date | None = _start,
    end_date: date | None = _end,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> CustomerDetailResponse:
    """Detalle del cliente: éxito/error, tiempo de atención en horas hábiles, tránsito
    logístico de Canal Directo, equipos y consumibles más pedidos."""
    use_case = build_get_customer_statistics(db)
    result = await use_case.execute(customer_id, days, start_date, end_date)
    return CustomerDetailResponse.from_result(result)
