"""Catálogo de reglas de alerta: listado y activar/desactivar (aplica en el
próximo re-análisis — el motor consulta las activas en cada corrida)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_regla_alerta_repository import (  # noqa: E501
    SqlAlchemyReglaAlertaRepository,
)
from src.modules.liquidaciones.presentation.config_routers._deps import (
    CATALOGO_SIZE,
    require_update,
    require_view,
)
from src.modules.liquidaciones.presentation.schemas.reglas_alerta_schemas import (
    ReglaActivaIn,
    ReglaAlertaOut,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


@router.get("/reglas-alerta", response_model=Page[ReglaAlertaOut])
async def list_reglas_alerta(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=CATALOGO_SIZE, ge=1, le=1000),
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[ReglaAlertaOut]:
    reglas = await SqlAlchemyReglaAlertaRepository(db).list_all()
    return Page.of([ReglaAlertaOut.from_entity(r) for r in reglas], page=page, size=size)


@router.patch("/reglas-alerta/{codigo}/activa", response_model=ReglaAlertaOut)
async def set_regla_activa(
    codigo: str,
    body: ReglaActivaIn,
    _: Identity = require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ReglaAlertaOut:
    regla = await SqlAlchemyReglaAlertaRepository(db).set_activa(codigo, body.activa)
    if regla is None:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return ReglaAlertaOut.from_entity(regla)
