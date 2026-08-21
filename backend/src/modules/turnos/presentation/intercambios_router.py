"""Intercambio de turnos (ADR-026): dos coberturas ADR-013 cruzadas que se
crean, editan y cancelan juntas. Router aparte porque `turnos_router.py`
ya supera el tamaño máximo de archivo (§4); mismo prefijo `/api/turnos` y
mismo permiso `turnos.manage` que el resto de las mutaciones del módulo
(ADR-029)."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.turnos.application.dtos.turno_dtos import IntercambioCommand
from src.modules.turnos.application.use_cases.cancel_intercambio import (
    CancelIntercambio,
    CancelIntercambioDependencies,
)
from src.modules.turnos.application.use_cases.create_intercambio import CreateIntercambio
from src.modules.turnos.application.use_cases.intercambio_support import (
    IntercambioDependencies,
)
from src.modules.turnos.application.use_cases.update_intercambio import UpdateIntercambio
from src.modules.turnos.domain.well_known_permissions import MANAGE
from src.modules.turnos.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_user_provider import (
    SqlAlchemyUserProvider,
)
from src.modules.turnos.presentation.schemas.intercambio_schemas import (
    IntercambioRequest,
    IntercambioResponse,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/turnos/intercambios", tags=["turnos"])

_require_manage = Depends(require_permission(MANAGE))


def _deps(db: AsyncSession) -> IntercambioDependencies:
    return IntercambioDependencies(
        overrides=SqlAlchemyAsignacionOverrideRepository(db),
        users=SqlAlchemyUserProvider(db),
    )


def _command(
    payload: IntercambioRequest,
    created_by_user_id: uuid.UUID,
    intercambio_id: uuid.UUID | None = None,
) -> IntercambioCommand:
    return IntercambioCommand(
        operador_a_id=payload.operador_a_id,
        operador_b_id=payload.operador_b_id,
        desde=payload.desde,
        hasta=payload.hasta,
        slot_ids_a=payload.slot_ids_a,
        slot_ids_b=payload.slot_ids_b,
        motivo=payload.motivo,
        created_by_user_id=created_by_user_id,
        intercambio_id=intercambio_id,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_intercambio(
    payload: IntercambioRequest,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> IntercambioResponse:
    dto = await CreateIntercambio(_deps(db)).execute(_command(payload, identity.user.id))
    return IntercambioResponse.from_dto(dto)


@router.put("/{intercambio_id}")
async def update_intercambio(
    intercambio_id: uuid.UUID,
    payload: IntercambioRequest,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> IntercambioResponse:
    # `created_by_user_id` del comando no se usa en la edición (se conserva el
    # del alta); se pasa el actual solo para completar el comando.
    dto = await UpdateIntercambio(_deps(db)).execute(
        _command(payload, identity.user.id, intercambio_id=intercambio_id)
    )
    return IntercambioResponse.from_dto(dto)


@router.post("/{intercambio_id}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_intercambio(
    intercambio_id: uuid.UUID,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    deps = CancelIntercambioDependencies(overrides=SqlAlchemyAsignacionOverrideRepository(db))
    await CancelIntercambio(deps).execute(intercambio_id)
