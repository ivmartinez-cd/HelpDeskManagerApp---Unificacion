import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.domain.well_known_permissions import MANAGE_ADMIN
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.turnos.application.dtos.turno_dtos import (
    CreateCasillaCommand,
    CreateSlotCommand,
    ReplaceAssignmentsCommand,
    UpdateCasillaCommand,
    UpdateSlotCommand,
)
from src.modules.turnos.application.use_cases.delete_casilla import (
    DeleteCasilla,
    DeleteCasillaDependencies,
)
from src.modules.turnos.application.use_cases.delete_slot import (
    DeleteSlot,
    DeleteSlotDependencies,
)
from src.modules.turnos.application.use_cases.get_current_shifts import (
    GetCurrentShifts,
    GetCurrentShiftsDependencies,
)
from src.modules.turnos.application.use_cases.list_casillas import (
    ListCasillas,
    ListCasillasDependencies,
)
from src.modules.turnos.application.use_cases.list_slots import (
    ListSlots,
    ListSlotsDependencies,
)
from src.modules.turnos.application.use_cases.replace_slot_assignments import (
    ReplaceSlotAssignments,
    ReplaceSlotAssignmentsDependencies,
)
from src.modules.turnos.application.use_cases.upsert_casilla import (
    UpsertCasilla,
    UpsertCasillaDependencies,
)
from src.modules.turnos.application.use_cases.upsert_slot import (
    UpsertSlot,
    UpsertSlotDependencies,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_asignacion_repository import (
    SqlAlchemyAsignacionRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_casilla_repository import (
    SqlAlchemyCasillaRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_slot_repository import (
    SqlAlchemySlotRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_user_provider import (
    SqlAlchemyUserProvider,
)
from src.modules.turnos.presentation.schemas.turno_schemas import (
    CasillaRequest,
    CasillaResponse,
    ReplaceAssignmentsRequest,
    ResolvedShiftResponse,
    SlotRequest,
    SlotResponse,
    UserOptionResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/turnos", tags=["turnos"])

# Catálogos chicos (2 casillas, ~35 slots hoy) -- paginados por contrato (CLAUDE.md
# §11) pero con default generoso porque alimentan la grilla del home/el panel de
# admin completo, no una tabla paginada.
_DEFAULT_SIZE = 200
_require_manage_admin = Depends(require_permission(MANAGE_ADMIN))


@router.get("/current")
async def get_current_shifts(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _identity: Identity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> Page[ResolvedShiftResponse]:
    deps = GetCurrentShiftsDependencies(
        casillas=SqlAlchemyCasillaRepository(db),
        slots=SqlAlchemySlotRepository(db),
        asignaciones=SqlAlchemyAsignacionRepository(db),
        users=SqlAlchemyUserProvider(db),
    )
    shifts = await GetCurrentShifts(deps).execute()
    return Page.of(
        [ResolvedShiftResponse.from_dto(s) for s in shifts], page=page, size=size
    )


@router.get("/casillas")
async def list_casillas(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> Page[CasillaResponse]:
    deps = ListCasillasDependencies(casillas=SqlAlchemyCasillaRepository(db))
    casillas = await ListCasillas(deps).execute(include_inactive=True)
    return Page.of([CasillaResponse.from_dto(c) for c in casillas], page=page, size=size)


@router.post("/casillas", status_code=status.HTTP_201_CREATED)
async def create_casilla(
    payload: CasillaRequest,
    _identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
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
    _identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
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
    _identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> None:
    deps = DeleteCasillaDependencies(casillas=SqlAlchemyCasillaRepository(db))
    await DeleteCasilla(deps).execute(casilla_id)


@router.get("/slots")
async def list_slots(
    casilla_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
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
    _identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
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
    _identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
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
    _identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
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
    _identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> None:
    deps = ReplaceSlotAssignmentsDependencies(asignaciones=SqlAlchemyAsignacionRepository(db))
    await ReplaceSlotAssignments(deps).execute(
        ReplaceAssignmentsCommand(
            slot_id=slot_id,
            user_ids=payload.user_ids,
            vigente_desde=payload.vigente_desde,
        )
    )


@router.get("/users")
async def list_assignable_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> Page[UserOptionResponse]:
    provider = SqlAlchemyUserProvider(db)
    users = await provider.list_all_active_users()
    return Page.of(
        [UserOptionResponse.from_info(u) for u in users], page=page, size=size
    )
