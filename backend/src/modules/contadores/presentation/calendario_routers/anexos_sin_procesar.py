"""KPI de Inicio "Anexos sin procesar" (resumen) y su pantalla de detalle.
Sin `try/except`: si Siges no responde, `ExternalServiceError` sube al
handler global (502) — el tile debe mostrar "sin dato", nunca un cero
inventado (ver `listar_anexos_sin_procesar.py`)."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.contadores.application.dtos.anexo_sin_procesar import (
    ResultadoAnexosSinProcesar,
)
from src.modules.contadores.application.use_cases.get_calendar_events import (
    GetCalendarEventsUseCase,
)
from src.modules.contadores.application.use_cases.get_pending_clients import (
    GetPendingClientsUseCase,
)
from src.modules.contadores.application.use_cases.listar_anexos_sin_procesar import (
    ListarAnexosSinProcesar,
)
from src.modules.contadores.application.use_cases.resumir_anexos_sin_procesar import (
    resumir_anexos_sin_procesar,
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
from src.modules.contadores.presentation.dependencies import get_estado_proceso_anexos_gateway
from src.modules.contadores.presentation.schemas.calendario_schemas import (
    AnexoSinProcesarSchema,
    AnexosSinProcesarResumenSchema,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


async def _resolver(
    db: AsyncSession, identity: Identity, today: date
) -> ResultadoAnexosSinProcesar:
    repo = SqlAlchemyCalendarEventRepository(db)
    overrides = SqlAlchemyAsignacionOverrideRepository(db)
    use_case = GetPendingClientsUseCase(GetCalendarEventsUseCase(repo, overrides), repo)
    anotados = await use_case.execute(
        is_superadmin=identity.user.is_superadmin,
        full_name=identity.user.full_name,
        today=today,
        cutoff_days=DEFAULT_BACKLOG_DAYS,
        exclude_operador_ids=POOL_BACKLOG_OPERADOR_IDS,
    )
    gateway = get_estado_proceso_anexos_gateway()
    return await ListarAnexosSinProcesar(gateway).execute(anotados, hoy=today)


@router.get(
    "/calendario/anexos-sin-procesar/resumen", response_model=AnexosSinProcesarResumenSchema
)
async def get_anexos_sin_procesar_resumen(
    today: str = Query(..., description="Hoy del operador, YYYY-MM-DD (huso local)"),
    identity: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AnexosSinProcesarResumenSchema:
    resultado = await _resolver(db, identity, date.fromisoformat(today))
    resumen = resumir_anexos_sin_procesar(resultado.anexos, consultado_en=resultado.consultado_en)
    return AnexosSinProcesarResumenSchema.model_validate(resumen)


@router.get("/calendario/anexos-sin-procesar", response_model=Page[AnexoSinProcesarSchema])
async def list_anexos_sin_procesar(
    today: str = Query(..., description="Hoy del operador, YYYY-MM-DD (huso local)"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=200, ge=1, le=MAX_PAGE_SIZE),
    identity: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[AnexoSinProcesarSchema]:
    resultado = await _resolver(db, identity, date.fromisoformat(today))
    schema_items = [AnexoSinProcesarSchema.model_validate(a) for a in resultado.anexos]
    return Page.of(schema_items, page=page, size=size)
