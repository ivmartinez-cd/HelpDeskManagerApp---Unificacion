"""Overrides temporales de asignación de operadores (ADR-013)."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.contadores.application.dtos.create_asignacion_override_request import (
    CreateAsignacionOverrideRequest as CreateAsignacionOverrideAppRequest,
)
from src.modules.contadores.application.dtos.update_asignacion_override_request import (
    UpdateAsignacionOverrideRequest as UpdateAsignacionOverrideAppRequest,
)
from src.modules.contadores.application.use_cases.cancel_asignacion_override import (
    CancelAsignacionOverride,
    CancelAsignacionOverrideDependencies,
)
from src.modules.contadores.application.use_cases.create_asignacion_override import (
    CreateAsignacionOverride,
    CreateAsignacionOverrideDependencies,
)
from src.modules.contadores.application.use_cases.list_asignacion_overrides import (
    ListAsignacionOverrides,
    ListAsignacionOverridesDependencies,
)
from src.modules.contadores.application.use_cases.update_asignacion_override import (
    UpdateAsignacionOverride,
    UpdateAsignacionOverrideDependencies,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.contadores.infrastructure.repositories.sqlalchemy_calendario_repository import (
    SqlAlchemyCalendarEventRepository,
)
from src.modules.contadores.presentation.calendario_routers._deps import (
    MAX_PAGE_SIZE,
    require_manage,
    require_view,
)
from src.modules.contadores.presentation.schemas.calendario_schemas import (
    AsignacionOverrideResponse,
    CreateAsignacionOverrideRequest,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter()


@router.get("/calendario/overrides", response_model=Page[AsignacionOverrideResponse])
async def list_overrides(
    _: Identity = require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[AsignacionOverrideResponse]:
    deps = ListAsignacionOverridesDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
        calendar=SqlAlchemyCalendarEventRepository(db),
    )
    items = await ListAsignacionOverrides(deps).execute()
    return Page.of(
        [AsignacionOverrideResponse.from_dto(i) for i in items], page=1, size=MAX_PAGE_SIZE
    )


@router.post(
    "/calendario/overrides",
    response_model=AsignacionOverrideResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_override(
    payload: CreateAsignacionOverrideRequest,
    identity: Identity = require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AsignacionOverrideResponse:
    deps = CreateAsignacionOverrideDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
        calendar=SqlAlchemyCalendarEventRepository(db),
    )
    dto = await CreateAsignacionOverride(deps).execute(
        CreateAsignacionOverrideAppRequest(
            operador_ausente_id=payload.operador_ausente_id,
            operador_reemplazante_id=payload.operador_reemplazante_id,
            vigente_desde=payload.vigente_desde,
            vigente_hasta=payload.vigente_hasta,
            clientes=payload.clientes,
            motivo=payload.motivo,
            created_by_user_id=identity.user.id,
        )
    )
    return AsignacionOverrideResponse.from_dto(dto)


@router.put("/calendario/overrides/{override_id}", response_model=AsignacionOverrideResponse)
async def update_override(
    override_id: uuid.UUID,
    # Mismo body que el alta — el id va en el path y el creador no cambia.
    payload: CreateAsignacionOverrideRequest,
    _: Identity = require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> AsignacionOverrideResponse:
    deps = UpdateAsignacionOverrideDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
        calendar=SqlAlchemyCalendarEventRepository(db),
    )
    dto = await UpdateAsignacionOverride(deps).execute(
        UpdateAsignacionOverrideAppRequest(
            override_id=override_id,
            operador_ausente_id=payload.operador_ausente_id,
            operador_reemplazante_id=payload.operador_reemplazante_id,
            vigente_desde=payload.vigente_desde,
            vigente_hasta=payload.vigente_hasta,
            clientes=payload.clientes,
            motivo=payload.motivo,
        )
    )
    return AsignacionOverrideResponse.from_dto(dto)


@router.post("/calendario/overrides/{override_id}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_override(
    override_id: uuid.UUID,
    _: Identity = require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    deps = CancelAsignacionOverrideDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db)
    )
    await CancelAsignacionOverride(deps).execute(override_id)
