"""Endpoints de la vista de gerencia — evolución mensual de un año calendario
completo, separados de `bono_tecnicos_router.py` (ya en el límite de tamaño
del §4) porque resuelven un caso de uso distinto (`GetEvolucionAnual`, no
`GetPuntajesPeriodo`)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.bono_tecnicos.application.dtos.evolucion_anual_dto import (
    GetEvolucionAnualRequest,
)
from src.modules.bono_tecnicos.domain.well_known_permissions import VIEW
from src.modules.bono_tecnicos.presentation.dependencies import build_get_evolucion_anual
from src.modules.bono_tecnicos.presentation.schemas.evolucion_anual_schemas import (
    EvolucionEquipoSchema,
    EvolucionTecnicoSchema,
    PuntoMensualSchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/bono-tecnicos", tags=["bono-tecnicos"])

_require_view = Depends(require_permission(VIEW))
# Mismo criterio que bono_tecnicos_router: ~27 técnicos entran en una página.
_MAX_PAGE_SIZE = 100
_anio = Query(..., ge=2000, le=2100, description="Año calendario, ej. 2026")


@router.get("/evolucion-anual", response_model=Page[EvolucionTecnicoSchema])
async def get_evolucion_anual(
    anio: int = _anio,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_MAX_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[EvolucionTecnicoSchema]:
    """Evolución mensual del año por técnico (puntaje, incidentes, TV
    solicitadas/aprobadas) — vista de gerencia. Una sola consulta anual
    cacheada contra Siges/ORION (ver `PyodbcConteoTecnicoGateway`), no 12
    llamadas mes a mes."""
    dto = await build_get_evolucion_anual(db).execute(GetEvolucionAnualRequest(anio=anio))
    items = [EvolucionTecnicoSchema.model_validate(t) for t in dto.tecnicos]
    return Page.of(items, page=page, size=size)


@router.get("/evolucion-anual/equipo", response_model=EvolucionEquipoSchema)
async def get_evolucion_equipo(
    anio: int = _anio,
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> EvolucionEquipoSchema:
    """Promedio mensual del equipo completo — la serie de referencia contra
    la que se compara cada técnico. No es una colección (es un resumen del
    año), por eso no va envuelta en `Page[T]` (mismo criterio que
    `insumos/presentation/statistics_router.py`)."""
    dto = await build_get_evolucion_anual(db).execute(GetEvolucionAnualRequest(anio=anio))
    return EvolucionEquipoSchema(
        anio=dto.anio,
        puntos=[PuntoMensualSchema.model_validate(p) for p in dto.equipo],
    )
