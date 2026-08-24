from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.bono_tecnicos.application.dtos.incidente_bono_dto import (
    GetIncidentesTecnicoRequest,
)
from src.modules.bono_tecnicos.application.dtos.puntaje_tecnico_dto import (
    GetPuntajesPeriodoRequest,
    GuardarBonoInputRequest,
)
from src.modules.bono_tecnicos.domain.well_known_permissions import UPDATE, VIEW
from src.modules.bono_tecnicos.presentation.dependencies import (
    build_get_incidentes_tecnico,
    build_get_puntajes_periodo,
    build_guardar_bono_input,
)
from src.modules.bono_tecnicos.presentation.schemas.incidente_bono_schemas import (
    IncidenteBonoSchema,
)
from src.modules.bono_tecnicos.presentation.schemas.puntaje_tecnico_schemas import (
    GuardarBonoInputBody,
    PuntajeTecnicoSchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/bono-tecnicos", tags=["bono-tecnicos"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
# ~27 técnicos de planta activos al 2026-08; una fila por técnico y período,
# entra entera en una sola página (mismo criterio que catálogos chicos, §11).
_MAX_PAGE_SIZE = 100
_periodo = Query(..., ge=200001, le=210012, description="Período mensual AAAAMM, ej. 202605")


@router.get("/resumen", response_model=Page[PuntajeTecnicoSchema])
async def get_resumen(
    periodo: int = _periodo,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_MAX_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[PuntajeTecnicoSchema]:
    """Resumen del bono del período: conteos por categoría (en vivo contra
    MERCURIO, sin cache) + Días/Tareas Varias cargados a mano + Puntaje.
    `puntaje` viene `null` mientras no se hayan cargado Días para ese
    técnico y período."""
    dtos = await build_get_puntajes_periodo(db).execute(GetPuntajesPeriodoRequest(periodo=periodo))
    items = [PuntajeTecnicoSchema.model_validate(d) for d in dtos]
    return Page.of(items, page=page, size=size)


@router.get("/{periodo}/{id_tecnico}/incidentes", response_model=Page[IncidenteBonoSchema])
async def get_incidentes(
    periodo: int,
    id_tecnico: int,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=200, ge=1, le=200),
    _: Identity = _require_view,
) -> Page[IncidenteBonoSchema]:
    """Detalle de incidentes de un técnico y período, agrupables por
    categoría en el cliente — equivalente a las tablas por categoría de
    "Tecnicos.xlsx" para ese técnico. En vivo contra MERCURIO, sin cache."""
    dtos = await build_get_incidentes_tecnico().execute(
        GetIncidentesTecnicoRequest(periodo=periodo, id_tecnico=id_tecnico)
    )
    items = [IncidenteBonoSchema.model_validate(d) for d in dtos]
    return Page.of(items, page=page, size=size)


@router.put("/{periodo}/{id_tecnico}", status_code=204)
async def guardar_input(
    periodo: int,
    id_tecnico: int,
    body: GuardarBonoInputBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    """Carga/corrige Días y Tareas Varias de un técnico en un período —
    reemplaza tipear a mano `Lista!$J$6`/`$J$7` en el Excel. El resumen
    recalculado se ve pidiendo de nuevo `GET /resumen`."""
    await build_guardar_bono_input(db).execute(
        GuardarBonoInputRequest(
            id_tecnico=id_tecnico,
            periodo=periodo,
            tecnico=body.tecnico,
            dias=body.dias,
            tareas_varias=body.tareas_varias,
        )
    )
