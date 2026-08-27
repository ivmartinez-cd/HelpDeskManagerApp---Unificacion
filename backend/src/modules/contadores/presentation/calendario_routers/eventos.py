"""Eventos del calendario: listado por rango, catálogo de operadores,
operador propio y backlog de pendientes."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.contadores.application.dtos.calendar_event_anotado import CalendarEventAnotado
from src.modules.contadores.application.dtos.get_calendar_events_request import (
    GetCalendarEventsRequest,
)
from src.modules.contadores.application.use_cases.filtrar_pendientes_por_periodo_real import (
    FiltrarPendientesPorPeriodoReal,
)
from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.application.use_cases.get_clientes_pendientes_periodo_actual import (
    GetClientesPendientesPeriodoActualUseCase,
)
from src.modules.contadores.application.use_cases.get_mi_operador import GetMiOperadorUseCase
from src.modules.contadores.application.use_cases.get_pending_clients import (
    GetPendingClientsUseCase,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)
from src.modules.contadores.presentation.calendario_routers._deps import (
    DEFAULT_BACKLOG_DAYS,
    MAX_PAGE_SIZE,
    POOL_BACKLOG_OPERADOR_IDS,
    require_view,
)
from src.modules.contadores.presentation.dependencies import (
    get_estado_cierre_grupos_gateway_or_none,
)
from src.modules.contadores.presentation.schemas.calendario_schemas import (
    CalendarEventSchema,
    MiOperadorResponse,
    OperadorSchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


@router.get("/calendario", response_model=Page[CalendarEventSchema])
async def get_calendario_events(
    start: str = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    end: str = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    operador_id: str | None = Query(
        default=None, description="Solo superadmin: filtra por un operador puntual"
    ),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=MAX_PAGE_SIZE),
    identity: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
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
    schema_events = [CalendarEventSchema.from_anotado(e) for e in events]
    return Page.of(schema_events, page=page, size=size)


@router.get("/calendario/operadores", response_model=Page[OperadorSchema])
async def get_calendario_operadores(
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[OperadorSchema]:
    """Catálogo local de operadores para alimentar el combobox de filtro del
    Calendario (solo superadmin lo usa — ver GetCalendarEventsUseCase)."""
    repo = SqlAlchemyCalendarEventRepository(db)
    operadores = await repo.list_operadores()
    schema_operadores = [OperadorSchema.model_validate(o) for o in operadores]
    return Page.of(schema_operadores, page=1, size=MAX_PAGE_SIZE)


@router.get("/calendario/mi-operador", response_model=MiOperadorResponse)
async def get_mi_operador(
    identity: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> MiOperadorResponse:
    repo = SqlAlchemyCalendarEventRepository(db)
    operador = await GetMiOperadorUseCase(repo).execute(
        is_superadmin=identity.user.is_superadmin, full_name=identity.user.full_name
    )
    if operador is None:
        return MiOperadorResponse(operador_id=None, nombre=None, color=None)
    return MiOperadorResponse(operador_id=operador.id, nombre=operador.nombre, color=operador.color)


@router.get("/calendario/pendientes", response_model=Page[CalendarEventSchema])
async def get_calendario_pendientes(
    today: str = Query(..., description="Hoy del operador, YYYY-MM-DD (huso local)"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=MAX_PAGE_SIZE),
    identity: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[CalendarEventSchema]:
    """Backlog de clientes de días anteriores que siguen en el calendario
    (pendientes de arrastre), cruzado contra el período real de Siges: si un
    cliente ya facturó o ya rodó al mes en curso, sale de la lista (ver
    FiltrarPendientesPorPeriodoReal). Misma visibilidad que GET /calendario."""
    repo = SqlAlchemyCalendarEventRepository(db)
    overrides = SqlAlchemyAsignacionOverrideRepository(db)
    use_case = GetPendingClientsUseCase(GetCalendarEventsUseCase(repo, overrides), repo)
    anotados = await use_case.execute(
        is_superadmin=identity.user.is_superadmin,
        full_name=identity.user.full_name,
        today=date.fromisoformat(today),
        cutoff_days=DEFAULT_BACKLOG_DAYS,
        exclude_operador_ids=POOL_BACKLOG_OPERADOR_IDS,
    )
    gateway = get_estado_cierre_grupos_gateway_or_none()
    if gateway is not None:
        anotados = await FiltrarPendientesPorPeriodoReal(gateway).execute(anotados)
    schema_events = [CalendarEventSchema.from_anotado(a) for a in anotados]
    return Page.of(schema_events, page=page, size=size)


def _build_pendientes_periodo_actual(
    db: AsyncSession,
) -> GetClientesPendientesPeriodoActualUseCase:
    repo = SqlAlchemyCalendarEventRepository(db)
    overrides = SqlAlchemyAsignacionOverrideRepository(db)
    return GetClientesPendientesPeriodoActualUseCase(
        GetPendingClientsUseCase(GetCalendarEventsUseCase(repo, overrides), repo)
    )


async def _filtrar_contra_siges(
    anotados: list[CalendarEventAnotado],
) -> list[CalendarEventAnotado]:
    gateway = get_estado_cierre_grupos_gateway_or_none()
    if gateway is None:
        return anotados
    return await FiltrarPendientesPorPeriodoReal(gateway).execute(anotados)


@router.get(
    "/calendario/pendientes-periodo-actual", response_model=Page[CalendarEventSchema]
)
async def get_clientes_pendientes_periodo_actual(
    today: str = Query(..., description="Hoy del operador, YYYY-MM-DD (huso local)"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=500, ge=1, le=MAX_PAGE_SIZE),
    identity: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[CalendarEventSchema]:
    """Clientes del período EN CURSO que todavía siguen en el calendario de
    Gestión, vencidos o no — un evento por cliente, cruzado contra Siges
    igual que /pendientes (ver `_filtrar_contra_siges`)."""
    anotados = await _build_pendientes_periodo_actual(db).execute(
        is_superadmin=identity.user.is_superadmin,
        full_name=identity.user.full_name,
        today=date.fromisoformat(today),
        exclude_operador_ids=POOL_BACKLOG_OPERADOR_IDS,
    )
    anotados = await _filtrar_contra_siges(anotados)
    schema_events = [CalendarEventSchema.from_anotado(a) for a in anotados]
    return Page.of(schema_events, page=page, size=size)
