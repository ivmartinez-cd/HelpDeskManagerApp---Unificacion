from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.wati.domain.well_known_permissions import UPDATE, VIEW
from src.modules.wati.presentation.dependencies import (
    build_get_pendientes_resumen,
    build_list_pendientes,
    build_sync_conversaciones,
)
from src.modules.wati.presentation.schemas.pendientes_schemas import (
    ConversacionPendienteSchema,
    OperadorPendientesSchema,
    PendientesResumenResponse,
    SyncResultadoResponse,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/wati/pendientes", tags=["wati-pendientes"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))
_MAX_PAGE_SIZE = 200


@router.get("/resumen", response_model=PendientesResumenResponse)
async def get_resumen(
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> PendientesResumenResponse:
    """Conteo de chats de WhatsApp esperando respuesta humana — lee el estado
    sincronizado por el job de fondo, nunca llama a WATI."""
    dto = await build_get_pendientes_resumen(db).execute()
    return PendientesResumenResponse(
        total=dto.total,
        sin_asignar=dto.sin_asignar,
        max_minutos_esperando=dto.max_minutos_esperando,
        por_operador=[OperadorPendientesSchema.model_validate(o) for o in dto.por_operador],
        sincronizado_at=dto.sincronizado_at,
        inbox_url=get_settings().wati_url or None,
    )


@router.get("", response_model=Page[ConversacionPendienteSchema])
async def list_pendientes(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_MAX_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[ConversacionPendienteSchema]:
    """Detalle de chats esperando respuesta, de la más antigua a la más nueva."""
    dtos = await build_list_pendientes(db).execute()
    items = [ConversacionPendienteSchema.model_validate(d) for d in dtos]
    return Page.of(items, page=page, size=size)


@router.post("/actualizar", response_model=SyncResultadoResponse)
async def actualizar(
    _identity: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> SyncResultadoResponse:
    """Fuerza un ciclo de sincronización contra la API de WATI (solo lectura
    del lado de WATI; consume cuota del rate limit)."""
    resultado = await build_sync_conversaciones(db).execute()
    await db.commit()
    return SyncResultadoResponse.model_validate(resultado)
