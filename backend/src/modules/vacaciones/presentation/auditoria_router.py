from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.features import require_feature
from src.modules.vacaciones.application.use_cases.listar_auditoria import (
    ListarAuditoria,
    ListarAuditoriaDependencies,
)
from src.modules.vacaciones.domain.repositories.auditoria import FiltrosAuditoria
from src.modules.vacaciones.domain.well_known_features import AUDITORIA
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_auditoria import (
    SqlAlchemyAuditoriaRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_user_directory import (
    SqlAlchemyUserDirectory,
)
from src.modules.vacaciones.presentation.schemas.auditoria_schemas import (
    RegistroAuditoriaResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/vacaciones/auditoria", tags=["vacaciones"])

_DEFAULT_SIZE = 50
# Función concedible por usuario (ADR-032): antes vacaciones.manage.
_require_manage = Depends(require_feature(AUDITORIA))


@router.get("")
async def list_auditoria(
    search: str | None = Query(default=None, max_length=100),
    entidad: str | None = Query(default=None, max_length=40),
    accion: str | None = Query(default=None, max_length=30),
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=200),
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[RegistroAuditoriaResponse]:
    deps = ListarAuditoriaDependencies(
        auditoria=SqlAlchemyAuditoriaRepository(db),
        users=SqlAlchemyUserDirectory(db),
    )
    filtros = FiltrosAuditoria(
        search=search, entidad=entidad, accion=accion, desde=desde, hasta=hasta
    )
    dtos, total = await ListarAuditoria(deps).execute(filtros, page=page, size=size)
    items = [RegistroAuditoriaResponse.from_dto(d) for d in dtos]
    return Page(items=items, total=total, page=page, size=size)
