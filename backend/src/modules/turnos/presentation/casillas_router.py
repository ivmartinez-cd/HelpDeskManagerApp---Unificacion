"""CRUD de casillas de turnos. Router aparte porque `turnos_router.py` ya
supera el tamaño máximo de archivo (§4); mismo prefijo `/api/turnos` y mismos
permisos `turnos.view`/`turnos.manage` que el resto del módulo (ADR-029)."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.turnos.application.dtos.turno_dtos import (
    CreateCasillaCommand,
    UpdateCasillaCommand,
)
from src.modules.turnos.application.use_cases.delete_casilla import (
    DeleteCasilla,
    DeleteCasillaDependencies,
)
from src.modules.turnos.application.use_cases.list_casillas import (
    ListCasillas,
    ListCasillasDependencies,
)
from src.modules.turnos.application.use_cases.upsert_casilla import (
    UpsertCasilla,
    UpsertCasillaDependencies,
)
from src.modules.turnos.domain.well_known_permissions import MANAGE, VIEW
from src.modules.turnos.infrastructure.repositories.sqlalchemy_casilla_repository import (
    SqlAlchemyCasillaRepository,
)
from src.modules.turnos.presentation.schemas.turno_schemas import (
    CasillaRequest,
    CasillaResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/turnos", tags=["turnos"])

# Catálogo chico (2 casillas hoy) -- paginado por contrato (CLAUDE.md §11) pero
# con default generoso porque alimenta la grilla del home/el panel de admin
# completo, no una tabla paginada.
_DEFAULT_SIZE = 200
_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))


@router.get("/casillas")
async def list_casillas(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[CasillaResponse]:
    deps = ListCasillasDependencies(casillas=SqlAlchemyCasillaRepository(db))
    casillas = await ListCasillas(deps).execute(include_inactive=True)
    return Page.of([CasillaResponse.from_dto(c) for c in casillas], page=page, size=size)


@router.post("/casillas", status_code=status.HTTP_201_CREATED)
async def create_casilla(
    payload: CasillaRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> CasillaResponse:
    deps = UpsertCasillaDependencies(casillas=SqlAlchemyCasillaRepository(db))
    c = await UpsertCasilla(deps).create(
        CreateCasillaCommand(
            nombre=payload.nombre,
            color=payload.color,
            sort_order=payload.sort_order,
            is_active=payload.is_active,
        )
    )
    return CasillaResponse.from_dto(c)


@router.put("/casillas/{casilla_id}")
async def update_casilla(
    casilla_id: uuid.UUID,
    payload: CasillaRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> CasillaResponse:
    # Solo `nombre` es editable acá -- ver el docstring de UpdateCasillaCommand.
    # `payload.color`/`sort_order`/`is_active` se ignoran a propósito (siguen
    # existiendo en CasillaRequest porque el POST sí los usa al crear).
    deps = UpsertCasillaDependencies(casillas=SqlAlchemyCasillaRepository(db))
    c = await UpsertCasilla(deps).update(
        UpdateCasillaCommand(casilla_id=casilla_id, nombre=payload.nombre)
    )
    return CasillaResponse.from_dto(c)


@router.delete("/casillas/{casilla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_casilla(
    casilla_id: uuid.UUID,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    deps = DeleteCasillaDependencies(casillas=SqlAlchemyCasillaRepository(db))
    await DeleteCasilla(deps).execute(casilla_id)
