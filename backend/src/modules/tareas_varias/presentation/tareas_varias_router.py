import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.tareas_varias.application.dtos.solicitud_tv_dto import (
    CrearSolicitudTvAdminRequest,
    CrearSolicitudTvPropiaRequest,
    DecidirSolicitudTvRequest,
    ListarSolicitudesTvPropiasRequest,
    ListarSolicitudesTvRequest,
)
from src.modules.tareas_varias.domain.well_known_permissions import APPROVE, CREATE
from src.modules.tareas_varias.presentation.dependencies import (
    build_crear_solicitud_tv_admin,
    build_crear_solicitud_tv_propia,
    build_decidir_solicitud_tv,
    build_listar_solicitudes_tv,
    build_listar_solicitudes_tv_propias,
)
from src.modules.tareas_varias.presentation.schemas.solicitud_tv_schemas import (
    CrearSolicitudTvAdminBody,
    CrearSolicitudTvBody,
    DecisionSolicitudTvBody,
    SolicitudTvSchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/tareas-varias", tags=["tareas-varias"])

_require_create = Depends(require_permission(CREATE))
_require_approve = Depends(require_permission(APPROVE))
# ~27 técnicos de planta activos al 2026-08; una fila por solicitud, entra
# entera en una sola página (mismo criterio que bono-tecnicos, §11).
_MAX_PAGE_SIZE = 100
_periodo = Query(..., ge=200001, le=210012, description="Período mensual AAAAMM, ej. 202605")


@router.post("", response_model=SolicitudTvSchema, status_code=201)
async def crear_solicitud_tv(
    body: CrearSolicitudTvBody,
    identity: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SolicitudTvSchema:
    """Alta de una solicitud de TV propia — reemplaza la fila que agregaba
    el Google Form al Sheet legacy. El técnico se resuelve del usuario
    autenticado (vínculo Empleado↔Siges); 404 si no está vinculado. Queda
    PENDIENTE hasta que un supervisor la decida; no impacta el Puntaje del
    bono hasta ser aprobada (ver `bono_tecnicos.TareasVariasGateway`)."""
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


@router.post(
    "/a-nombre-de/{id_tecnico}",
    response_model=SolicitudTvSchema,
    status_code=201,
)
async def crear_solicitud_tv_admin(
    id_tecnico: int,
    body: CrearSolicitudTvAdminBody,
    identity: Identity = _require_approve,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SolicitudTvSchema:
    """Carga de TV por un supervisor a nombre de cualquier técnico — nace ya
    APROBADA, a diferencia de `POST /` (ver dependencies)."""
    request = CrearSolicitudTvAdminRequest(
        id_tecnico=id_tecnico,
        tecnico=body.tecnico,
        fecha=body.fecha,
        razon_social=body.razon_social,
        sucursal=body.sucursal,
        tarea_realizada=body.tarea_realizada,
        resuelta_por_email=identity.user.email,
    )
    dto = await build_crear_solicitud_tv_admin(db).execute(request)
    return SolicitudTvSchema.model_validate(dto)


@router.get("/mias", response_model=Page[SolicitudTvSchema])
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


@router.get("", response_model=Page[SolicitudTvSchema])
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


@router.patch("/{solicitud_id}/decision", response_model=SolicitudTvSchema)
async def decidir_solicitud_tv(
    solicitud_id: uuid.UUID,
    body: DecisionSolicitudTvBody,
    identity: Identity = _require_approve,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SolicitudTvSchema:
    """Aprobar/rechazar una solicitud de TV. Solo las APROBADA cuentan en el
    Puntaje del bono del período (ver `bono_tecnicos.TareasVariasGateway`)."""
    dto = await build_decidir_solicitud_tv(db).execute(
        DecidirSolicitudTvRequest(
            solicitud_id=solicitud_id,
            decision=body.decision,
            motivo=body.motivo,
            resuelta_por_email=identity.user.email,
        )
    )
    return SolicitudTvSchema.model_validate(dto)
