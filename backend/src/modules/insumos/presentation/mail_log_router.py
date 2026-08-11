"""Endpoint de consulta del registro de mails salientes de la app."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.domain.well_known_permissions import VIEW
from src.modules.insumos.presentation.dependencies import build_list_mail_log
from src.modules.insumos.presentation.schemas.mail_log_schemas import MailLogRowOut
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))


@router.get("/mail-log", response_model=Page[MailLogRowOut])
async def list_mail_log(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=100, ge=1, le=500),
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[MailLogRowOut]:
    """Últimos mails enviados (o intentados) por la app: backup diario, alerta de
    poller caído/recuperado y aviso de pedidos Pendientes por vencer. Paginado en SQL
    — la tabla nunca se poda."""
    entries, total = await build_list_mail_log(db).execute(page=page, size=size)
    return Page(
        items=[MailLogRowOut.from_entry(e) for e in entries],
        total=total,
        page=page,
        size=size,
    )
