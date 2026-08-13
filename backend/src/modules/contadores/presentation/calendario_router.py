import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.application.dtos.create_asignacion_override_request import (
    CreateAsignacionOverrideRequest as CreateAsignacionOverrideAppRequest,
)
from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.application.use_cases.cancel_asignacion_override import (
    CancelAsignacionOverride,
    CancelAsignacionOverrideDependencies,
)
from src.modules.contadores.application.use_cases.create_asignacion_override import (
    CreateAsignacionOverride,
    CreateAsignacionOverrideDependencies,
)
from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.application.use_cases.get_mi_operador import GetMiOperadorUseCase
from src.modules.contadores.application.use_cases.list_asignacion_overrides import (
    ListAsignacionOverrides,
    ListAsignacionOverridesDependencies,
)
from src.modules.contadores.application.use_cases.sync_calendar_events import (
    SyncCalendarEventsUseCase,
)
from src.modules.contadores.domain.well_known_permissions import MANAGE, VIEW
from src.modules.contadores.infrastructure.gestion.gestion_planificacion_client import (
    GestionPlanificacionClient,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)
from src.modules.contadores.presentation.dependencies import get_operador_catalog_gateway
from src.modules.contadores.presentation.schemas.calendario_schemas import (
    AsignacionOverrideResponse,
    CalendarEventSchema,
    CreateAsignacionOverrideRequest,
    MiOperadorResponse,
    OperadorSchema,
    SyncCalendarioResponse,
    SyncStatusResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/contadores", tags=["contadores-calendario"])

_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))
# Un mes con muchos eventos de facturación no debería superar esto; si algún
# rango lo hace, subir el tope antes que silenciar la paginación.
_MAX_PAGE_SIZE = 2000
# Ventana por defecto de "Sincronizar": Gestión no entrega un diff, así que
# cada sync rehace este rango entero con UN pedido sin filtro (los eventos ya
# traen su operador — ver SyncCalendarEventsUseCase). ajax-by-rango se pone
# lento en rangos muy anchos — medido a mano: ~5s para 1 mes, ~20s para 180
# días, supera los 45s con más de un año. 90 días para cada lado cubre "todo
# lo vigente" quedando cómodo dentro del timeout.
_DEFAULT_SYNC_WINDOW_DAYS = 90
# Generoso a propósito: es una acción manual e infrecuente, no un fetch de
# página — 2.2x el tiempo medido del pedido de 180 días, con margen para los
# días en que Gestión anda lenta.
_SYNC_TIMEOUT_SECONDS = 45.0


@router.get("/calendario", response_model=Page[CalendarEventSchema])
async def get_calendario_events(
    start: str = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end: str = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    operador_id: str | None = Query(
        default=None, description="Solo superadmin: filtra por un operador puntual"
    ),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=_MAX_PAGE_SIZE),
    identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[CalendarEventSchema]:
    repo = SqlAlchemyCalendarEventRepository(db)
    overrides = SqlAlchemyAsignacionOverrideRepository(db)
    request = GetCalendarEventsRequest(
        start_date=start,
        end_date=end,
        is_superadmin=identity.user.is_superadmin,
        full_name=identity.user.full_name,
        operador_id=operador_id,
    )
    events = await GetCalendarEventsUseCase(repo, overrides).execute(request)
    schema_events = [CalendarEventSchema.model_validate(e) for e in events]
    return Page.of(schema_events, page=page, size=size)


@router.get("/calendario/operadores", response_model=Page[OperadorSchema])
async def get_calendario_operadores(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[OperadorSchema]:
    """Catálogo local de operadores para alimentar el combobox de filtro del
    Calendario (solo superadmin lo usa — ver GetCalendarEventsUseCase)."""
    repo = SqlAlchemyCalendarEventRepository(db)
    operadores = await repo.list_operadores()
    schema_operadores = [OperadorSchema.model_validate(o) for o in operadores]
    return Page.of(schema_operadores, page=1, size=_MAX_PAGE_SIZE)


@router.get("/calendario/mi-operador", response_model=MiOperadorResponse)
async def get_mi_operador(
    identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> MiOperadorResponse:
    repo = SqlAlchemyCalendarEventRepository(db)
    operador = await GetMiOperadorUseCase(repo).execute(
        is_superadmin=identity.user.is_superadmin, full_name=identity.user.full_name
    )
    if operador is None:
        return MiOperadorResponse(operador_id=None, nombre=None, color=None)
    return MiOperadorResponse(operador_id=operador.id, nombre=operador.nombre, color=operador.color)


@router.get("/calendario/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> SyncStatusResponse:
    repo = SqlAlchemyCalendarEventRepository(db)
    last_synced_at = await repo.last_synced_at()
    total_events = await repo.count_events()
    return SyncStatusResponse(last_synced_at=last_synced_at, total_events=total_events)


@router.post("/calendario/sync", response_model=SyncCalendarioResponse)
async def sync_calendario(
    _: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> SyncCalendarioResponse:
    today = datetime.now(UTC).date()
    window = timedelta(days=_DEFAULT_SYNC_WINDOW_DAYS)
    start_date = (today - window).isoformat()
    end_date = (today + window).isoformat()

    repo = SqlAlchemyCalendarEventRepository(db)
    gestion = GestionPlanificacionClient(timeout=_SYNC_TIMEOUT_SECONDS)
    operador_catalog = get_operador_catalog_gateway()
    use_case = SyncCalendarEventsUseCase(gestion, operador_catalog, repo)
    result = await use_case.execute(start_date=start_date, end_date=end_date)
    return SyncCalendarioResponse.model_validate(result)


@router.get("/calendario/overrides", response_model=Page[AsignacionOverrideResponse])
async def list_overrides(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[AsignacionOverrideResponse]:
    deps = ListAsignacionOverridesDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
        calendar=SqlAlchemyCalendarEventRepository(db),
    )
    items = await ListAsignacionOverrides(deps).execute()
    return Page.of(
        [AsignacionOverrideResponse.from_dto(i) for i in items], page=1, size=_MAX_PAGE_SIZE
    )


@router.post(
    "/calendario/overrides",
    response_model=AsignacionOverrideResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_override(
    payload: CreateAsignacionOverrideRequest,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> AsignacionOverrideResponse:
    deps = CreateAsignacionOverrideDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
        calendar=SqlAlchemyCalendarEventRepository(db),
    )
    dto = await CreateAsignacionOverride(deps).execute(
        CreateAsignacionOverrideAppRequest(
            operador_ausente_id=payload.operador_ausente_id,
            operador_reemplazante_id=payload.operador_reemplazante_id,
            vigente_desde=payload.vigente_desde,
            vigente_hasta=payload.vigente_hasta,
            clientes=payload.clientes,
            motivo=payload.motivo,
            created_by_user_id=identity.user.id,
        )
    )
    return AsignacionOverrideResponse.from_dto(dto)


@router.post("/calendario/overrides/{override_id}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_override(
    override_id: uuid.UUID,
    _: Identity = _require_manage,
    db: AsyncSession = Depends(get_db),
) -> None:
    deps = CancelAsignacionOverrideDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db)
    )
    await CancelAsignacionOverride(deps).execute(override_id)
