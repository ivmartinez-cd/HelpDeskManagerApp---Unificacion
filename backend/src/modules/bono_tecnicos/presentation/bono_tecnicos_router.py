import uuid

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
from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import (
    CrearSolicitudTvPropiaRequest,
    DecidirSolicitudTvRequest,
    ListarSolicitudesTvPropiasRequest,
    ListarSolicitudesTvRequest,
)
from src.modules.bono_tecnicos.domain.well_known_permissions import APPROVE, CREATE, UPDATE, VIEW
from src.modules.bono_tecnicos.presentation.dependencies import (
    build_crear_solicitud_tv_propia,
    build_decidir_solicitud_tv,
    build_get_incidentes_tecnico,
    build_get_puntajes_periodo,
    build_guardar_bono_input,
    build_listar_solicitudes_tv,
    build_listar_solicitudes_tv_propias,
)
from src.modules.bono_tecnicos.presentation.schemas.incidente_bono_schemas import (
    IncidenteBonoSchema,
)
from src.modules.bono_tecnicos.presentation.schemas.puntaje_tecnico_schemas import (
    GuardarBonoInputBody,
    PuntajeTecnicoSchema,
)
from src.modules.bono_tecnicos.presentation.schemas.solicitud_tv_schemas import (
    CrearSolicitudTvBody,
    DecisionSolicitudTvBody,
    SolicitudTvSchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/bono-tecnicos", tags=["bono-tecnicos"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_require_create = Depends(require_permission(CREATE))
_require_approve = Depends(require_permission(APPROVE))
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
    mano `Lista!$J$6` en el Excel. Tareas Varias ya no se carga acá (ver
    `POST/PATCH .../solicitudes-tv`). El resumen recalculado se ve pidiendo
    de nuevo `GET /resumen`."""
    await build_guardar_bono_input(db).execute(
        GuardarBonoInputRequest(
            id_tecnico=id_tecnico,
            periodo=periodo,
            tecnico=body.tecnico,
            dias=body.dias,
        )
    )


@router.post("/solicitudes-tv", response_model=SolicitudTvSchema, status_code=201)
async def crear_solicitud_tv(
    body: CrearSolicitudTvBody,
    identity: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SolicitudTvSchema:
    """Alta de una solicitud de TV propia — reemplaza la fila que agregaba
    el Google Form al Sheet legacy. El técnico se resuelve del usuario
    autenticado (vínculo Empleado↔Siges); 404 si no está vinculado. Queda
    PENDIENTE hasta que un supervisor la decida; no impacta el Puntaje hasta
    ser aprobada."""
    dto = await build_crear_solicitud_tv_propia(db).execute(
        CrearSolicitudTvPropiaRequest(
            user_id=identity.user.id,
            fecha=body.fecha,
            razon_social=body.razon_social,
            sucursal=body.sucursal,
            tarea_realizada=body.tarea_realizada,
        )
    )
    return SolicitudTvSchema.model_validate(dto)


@router.get("/solicitudes-tv/mias", response_model=Page[SolicitudTvSchema])
async def listar_mis_solicitudes_tv(
    periodo: int = _periodo,
    estado: str | None = Query(default=None, pattern="^(PENDIENTE|APROBADA|RECHAZADA)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_MAX_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    identity: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[SolicitudTvSchema]:
    """Historial de solicitudes de TV del técnico autenticado — forzado a su
    propio `id_tecnico`, nunca a uno pedido por el cliente."""
    dtos = await build_listar_solicitudes_tv_propias(db).execute(
        ListarSolicitudesTvPropiasRequest(
            user_id=identity.user.id, periodo=periodo, estado=estado
        )
    )
    items = [SolicitudTvSchema.model_validate(d) for d in dtos]
    return Page.of(items, page=page, size=size)


@router.get("/solicitudes-tv", response_model=Page[SolicitudTvSchema])
async def listar_solicitudes_tv(
    periodo: int = _periodo,
    estado: str | None = Query(default=None, pattern="^(PENDIENTE|APROBADA|RECHAZADA)$"),
    id_tecnico: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_MAX_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    _: Identity = _require_approve,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[SolicitudTvSchema]:
    """Cola de aprobación del supervisor: todas las solicitudes de TV de un
    período, opcionalmente filtradas por estado o técnico."""
    dtos = await build_listar_solicitudes_tv(db).execute(
        ListarSolicitudesTvRequest(periodo=periodo, estado=estado, id_tecnico=id_tecnico)
    )
    items = [SolicitudTvSchema.model_validate(d) for d in dtos]
    return Page.of(items, page=page, size=size)


@router.patch("/solicitudes-tv/{solicitud_id}/decision", response_model=SolicitudTvSchema)
async def decidir_solicitud_tv(
    solicitud_id: uuid.UUID,
    body: DecisionSolicitudTvBody,
    identity: Identity = _require_approve,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SolicitudTvSchema:
    """Aprobar/rechazar una solicitud de TV. Solo las APROBADA cuentan en el
    Puntaje del período (`GET /resumen`)."""
    dto = await build_decidir_solicitud_tv(db).execute(
        DecidirSolicitudTvRequest(
            solicitud_id=solicitud_id,
            decision=body.decision,
            motivo=body.motivo,
            resuelta_por_email=identity.user.email,
        )
    )
    return SolicitudTvSchema.model_validate(dto)
