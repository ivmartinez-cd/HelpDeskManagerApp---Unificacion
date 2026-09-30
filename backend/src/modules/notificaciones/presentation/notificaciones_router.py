"""Bandeja de notificaciones del usuario logueado (campanita del header).

Repo directo, sin use case (mismo criterio que `modificaciones_router.py` de
liquidaciones): no hay regla de negocio más allá de filtrar por audiencia y
paginar. Solo exige sesión, no un permiso de módulo: cada uno ve únicamente
las notificaciones dirigidas a sus funciones/permisos; el superadmin, todas."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.notificaciones.domain.repositories.notificacion_repository import Audiencias
from src.modules.notificaciones.domain.value_objects.audiencia import audiencias_de
from src.modules.notificaciones.infrastructure.repositories.sqlalchemy_notificacion_repository import (  # noqa: E501
    SqlAlchemyNotificacionRepository,
)
from src.modules.notificaciones.presentation.schemas.notificacion_schemas import (
    MarcarLeidasIn,
    MarcarLeidasOut,
    NotificacionOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/notificaciones", tags=["notificaciones"])

_identity = Depends(get_current_identity)


def _audiencias(identity: Identity) -> Audiencias:
    if identity.user.is_superadmin:
        return None
    permisos = frozenset((p.module, p.action) for p in identity.permissions)
    return audiencias_de(identity.features, permisos)


@router.get("", response_model=Page[NotificacionOut])
async def listar_notificaciones(
    solo_no_leidas: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    identity: Identity = _identity,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[NotificacionOut]:
    """Más recientes primero. Con `solo_no_leidas`, `total` es el número del
    badge de la campanita."""
    items, total = await SqlAlchemyNotificacionRepository(db).listar(
        identity.user.id,
        _audiencias(identity),
        solo_no_leidas=solo_no_leidas,
        offset=(page - 1) * size,
        limit=size,
    )
    return Page(
        items=[NotificacionOut.from_entity(n) for n in items], total=total, page=page, size=size
    )


@router.post("/marcar-leidas", response_model=MarcarLeidasOut)
async def marcar_leidas(
    body: MarcarLeidasIn,
    identity: Identity = _identity,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> MarcarLeidasOut:
    actualizadas = await SqlAlchemyNotificacionRepository(db).marcar_leidas(
        identity.user.id, _audiencias(identity), body.ids
    )
    return MarcarLeidasOut(actualizadas=actualizadas)
