from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.bono_tecnicos.application.dtos.incidente_bono_dto import (
    GetIncidentesTecnicoRequest,
)
from src.modules.bono_tecnicos.application.dtos.puntaje_tecnico_dto import (
    GetMiResumenBonoRequest,
    GetPuntajesPeriodoRequest,
    GuardarBonoInputRequest,
)
from src.modules.bono_tecnicos.domain.well_known_permissions import CREATE, UPDATE, VIEW
from src.modules.bono_tecnicos.presentation.dependencies import (
    build_get_incidentes_tecnico,
    build_get_mi_resumen_bono,
    build_get_puntajes_periodo,
    build_get_vinculo_siges,
    build_guardar_bono_input,
)
from src.modules.bono_tecnicos.presentation.schemas.incidente_bono_schemas import (
    IncidenteBonoSchema,
)
from src.modules.bono_tecnicos.presentation.schemas.puntaje_tecnico_schemas import (
    GuardarBonoInputBody,
    MiResumenBonoSchema,
    PuntajeTecnicoSchema,
    VinculoSigesSchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/bono-tecnicos", tags=["bono-tecnicos"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_require_create = Depends(require_permission(CREATE))
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
    """Carga/corrige Días de un técnico en un período — reemplaza tipear a
    mano `Lista!$J$6` en el Excel. Tareas Varias se carga en el módulo
    `tareas_varias` (`POST/PATCH /api/tareas-varias/...`). El resumen
    recalculado se ve pidiendo de nuevo `GET /resumen`."""
    await build_guardar_bono_input(db).execute(
        GuardarBonoInputRequest(
            id_tecnico=id_tecnico,
            periodo=periodo,
            tecnico=body.tecnico,
            dias=body.dias,
        )
    )


@router.get("/vinculo-siges", response_model=VinculoSigesSchema)
async def get_vinculo_siges(
    identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db, scope="function"),
) -> VinculoSigesSchema:
    """Si el usuario autenticado tiene vínculo Empleado↔Siges — para que el
    frontend decida si corresponde mostrar "Mi bono"/Tareas Varias antes de
    pedir `/mi-resumen` (404 si no hay vínculo). Sin permiso específico: un
    superadmin ve todos los módulos (`ListVisibleModules`) y dispararía ese
    404 aunque no sea técnico si esto exigiera `bono-tecnicos.create`."""
    vinculado = await build_get_vinculo_siges(db).execute(identity.user.id)
    return VinculoSigesSchema(vinculado=vinculado)


@router.get("/mi-resumen", response_model=MiResumenBonoSchema)
async def get_mi_resumen(
    periodo: int | None = Query(default=None, ge=200001, le=210012),
    identity: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> MiResumenBonoSchema:
    """Puntaje/conteos/TV del técnico autenticado en un período — default el
    mes en curso. Para el card "Mi bono" de Inicio y Bono Técnicos. 404 si
    el usuario no está vinculado a un técnico de Siges
    (`TecnicoNoVinculadoError`)."""
    periodo_efectivo = periodo or int(date.today().strftime("%Y%m"))
    dto = await build_get_mi_resumen_bono(db).execute(
        GetMiResumenBonoRequest(user_id=identity.user.id, periodo=periodo_efectivo)
    )
    return MiResumenBonoSchema.model_validate(dto)
