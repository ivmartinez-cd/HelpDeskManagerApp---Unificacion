"""CRUD de slots de turnos y reasignación de operadores. Router aparte porque
`turnos_router.py` ya supera el tamaño máximo de archivo (§4); mismo prefijo
`/api/turnos` y mismos permisos `turnos.view`/`turnos.manage` que el resto del
módulo (ADR-029)."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.turnos.application.dtos.turno_dtos import (
    CreateSlotCommand,
    ReplaceAssignmentsCommand,
    UpdateSlotCommand,
)
from src.modules.turnos.application.use_cases.delete_slot import (
    DeleteSlot,
    DeleteSlotDependencies,
)
from src.modules.turnos.application.use_cases.list_slots import (
    ListSlots,
    ListSlotsDependencies,
)
from src.modules.turnos.application.use_cases.replace_slot_assignments import (
    ReplaceSlotAssignments,
    ReplaceSlotAssignmentsDependencies,
)
from src.modules.turnos.application.use_cases.upsert_slot import (
    UpsertSlot,
    UpsertSlotDependencies,
)
from src.modules.turnos.domain.well_known_permissions import MANAGE, VIEW
from src.modules.turnos.infrastructure.repositories.sqlalchemy_asignacion_repository import (
    SqlAlchemyAsignacionRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_slot_repository import (
    SqlAlchemySlotRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_user_provider import (
    SqlAlchemyUserProvider,
)
from src.modules.turnos.presentation.schemas.turno_schemas import (
    ReplaceAssignmentsRequest,
    SlotRequest,
    SlotResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/turnos", tags=["turnos"])

# Catálogo chico (~35 slots hoy) -- paginado por contrato (CLAUDE.md §11) pero
# con default generoso porque alimenta la grilla del home/el panel de admin
# completo, no una tabla paginada.
_DEFAULT_SIZE = 200
_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))


@router.get("/slots")
async def list_slots(
    casilla_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[SlotResponse]:
    deps = ListSlotsDependencies(
        slots=SqlAlchemySlotRepository(db),
        asignaciones=SqlAlchemyAsignacionRepository(db),
        users=SqlAlchemyUserProvider(db),
    )
    slots = await ListSlots(deps).execute(casilla_id=casilla_id)
    return Page.of([SlotResponse.from_dto(s) for s in slots], page=page, size=size)


@router.post("/slots", status_code=status.HTTP_201_CREATED)
async def create_slot(
    payload: SlotRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SlotResponse:
    deps = UpsertSlotDependencies(slots=SqlAlchemySlotRepository(db))
    s = await UpsertSlot(deps).create(
        CreateSlotCommand(
            casilla_id=payload.casilla_id,
            hora_inicio=payload.hora_inicio,
            hora_fin=payload.hora_fin,
            dia_semana=payload.dia_semana,
            sort_order=payload.sort_order,
        )
    )
    return SlotResponse.from_dto(s)


@router.put("/slots/{slot_id}")
async def update_slot(
    slot_id: uuid.UUID,
    payload: SlotRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> SlotResponse:
    # `payload.sort_order` se ignora a propósito -- ver UpdateSlotCommand.
    deps = UpsertSlotDependencies(slots=SqlAlchemySlotRepository(db))
    s = await UpsertSlot(deps).update(
        UpdateSlotCommand(
            slot_id=slot_id,
            hora_inicio=payload.hora_inicio,
            hora_fin=payload.hora_fin,
            dia_semana=payload.dia_semana,
        )
    )
    return SlotResponse.from_dto(s)


@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(
    slot_id: uuid.UUID,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    deps = DeleteSlotDependencies(
        slots=SqlAlchemySlotRepository(db),
        asignaciones=SqlAlchemyAsignacionRepository(db),
    )
    await DeleteSlot(deps).execute(slot_id)


@router.post("/slots/{slot_id}/asignaciones", status_code=status.HTTP_204_NO_CONTENT)
async def replace_slot_assignments(
    slot_id: uuid.UUID,
    payload: ReplaceAssignmentsRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    deps = ReplaceSlotAssignmentsDependencies(asignaciones=SqlAlchemyAsignacionRepository(db))
    await ReplaceSlotAssignments(deps).execute(
        ReplaceAssignmentsCommand(
            slot_id=slot_id,
            user_ids=payload.user_ids,
            vigente_desde=payload.vigente_desde,
        )
    )
