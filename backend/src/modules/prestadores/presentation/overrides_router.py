"""Endpoints de overrides temporales de asignación (ver ADR-013) —
sub-router anidado bajo /api/prestadores (lo incluye `prestadores_router`,
que aporta el prefijo)."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.prestadores.application.dtos.prestador_dtos import (
    CreateAsignacionOverrideCommand,
)
from src.modules.prestadores.application.use_cases.cancel_asignacion_override import (
    CancelAsignacionOverride,
    CancelAsignacionOverrideDependencies,
)
from src.modules.prestadores.application.use_cases.create_asignacion_override import (
    CreateAsignacionOverride,
    CreateAsignacionOverrideDependencies,
)
from src.modules.prestadores.application.use_cases.list_asignacion_overrides import (
    ListAsignacionOverrides,
    ListAsignacionOverridesDependencies,
)
from src.modules.prestadores.domain.well_known_permissions import CREATE, UPDATE, VIEW
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_user_provider import (
    SqlAlchemyUserProvider,
)
from src.modules.prestadores.presentation.schemas.prestador_schemas import (
    AsignacionOverrideResponse,
    CreateAsignacionOverrideRequest,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()

_require_view = Depends(require_permission(VIEW))
_require_create = Depends(require_permission(CREATE))
_require_update = Depends(require_permission(UPDATE))
# Catálogo chico (ABM manual, no una tabla transaccional) — mismo criterio
# que /operadores y /historial.
_DEFAULT_SIZE = 200


@router.get("/overrides")
async def list_overrides(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> Page[AsignacionOverrideResponse]:
    deps = ListAsignacionOverridesDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
        users=SqlAlchemyUserProvider(db),
    )
    items = await ListAsignacionOverrides(deps).execute()
    return Page.of(
        [AsignacionOverrideResponse.from_dto(i) for i in items], page=1, size=_DEFAULT_SIZE
    )


@router.post("/overrides", status_code=status.HTTP_201_CREATED)
async def create_override(
    payload: CreateAsignacionOverrideRequest,
    identity: Identity = _require_create,
    db: AsyncSession = Depends(get_db),
) -> AsignacionOverrideResponse:
    deps = CreateAsignacionOverrideDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
        users=SqlAlchemyUserProvider(db),
    )
    dto = await CreateAsignacionOverride(deps).execute(
        CreateAsignacionOverrideCommand(
            operador_ausente_id=payload.operador_ausente_id,
            operador_reemplazante_id=payload.operador_reemplazante_id,
            desde=payload.desde,
            hasta=payload.hasta,
            prestador_ids=payload.prestador_ids,
            motivo=payload.motivo,
            created_by_user_id=identity.user.id,
        )
    )
    return AsignacionOverrideResponse.from_dto(dto)


@router.post("/overrides/{override_id}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_override(
    override_id: uuid.UUID,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> None:
    deps = CancelAsignacionOverrideDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db)
    )
    await CancelAsignacionOverride(deps).execute(override_id)
