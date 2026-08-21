"""CRUD de overrides de asignación (reemplazos temporales). Router aparte
porque `turnos_router.py` ya supera el tamaño máximo de archivo (§4); mismo
prefijo `/api/turnos` y mismos permisos `turnos.view`/`turnos.manage` que el
resto del módulo (ADR-029)."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.turnos.application.dtos.turno_dtos import (
    CreateAsignacionOverrideCommand,
    UpdateAsignacionOverrideCommand,
)
from src.modules.turnos.application.use_cases.cancel_asignacion_override import (
    CancelAsignacionOverride,
    CancelAsignacionOverrideDependencies,
)
from src.modules.turnos.application.use_cases.create_asignacion_override import (
    CreateAsignacionOverride,
    CreateAsignacionOverrideDependencies,
)
from src.modules.turnos.application.use_cases.list_asignacion_overrides import (
    ListAsignacionOverrides,
    ListAsignacionOverridesDependencies,
)
from src.modules.turnos.application.use_cases.update_asignacion_override import (
    UpdateAsignacionOverride,
    UpdateAsignacionOverrideDependencies,
)
from src.modules.turnos.domain.well_known_permissions import MANAGE, VIEW
from src.modules.turnos.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_user_provider import (
    SqlAlchemyUserProvider,
)
from src.modules.turnos.presentation.schemas.turno_schemas import (
    AsignacionOverrideResponse,
    CreateAsignacionOverrideRequest,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/turnos", tags=["turnos"])

_DEFAULT_SIZE = 200
_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))


@router.get("/overrides")
async def list_overrides(
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
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
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
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
            slot_ids=payload.slot_ids,
            motivo=payload.motivo,
            created_by_user_id=identity.user.id,
        )
    )
    return AsignacionOverrideResponse.from_dto(dto)


@router.put("/overrides/{override_id}")
async def update_override(
    override_id: uuid.UUID,
    # Mismo body que el alta -- el id va en el path y el creador no cambia.
    payload: CreateAsignacionOverrideRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AsignacionOverrideResponse:
    deps = UpdateAsignacionOverrideDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
        users=SqlAlchemyUserProvider(db),
    )
    dto = await UpdateAsignacionOverride(deps).execute(
        UpdateAsignacionOverrideCommand(
            override_id=override_id,
            operador_ausente_id=payload.operador_ausente_id,
            operador_reemplazante_id=payload.operador_reemplazante_id,
            desde=payload.desde,
            hasta=payload.hasta,
            slot_ids=payload.slot_ids,
            motivo=payload.motivo,
        )
    )
    return AsignacionOverrideResponse.from_dto(dto)


@router.post("/overrides/{override_id}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_override(
    override_id: uuid.UUID,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    deps = CancelAsignacionOverrideDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db)
    )
    await CancelAsignacionOverride(deps).execute(override_id)
