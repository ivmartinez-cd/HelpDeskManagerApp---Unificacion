"""Modo vacaciones (ADR-025): grillas variantes de turnos. Router aparte
porque `turnos_router.py` ya supera el tamaño máximo de archivo (§4); mismo
prefijo `/api/turnos` y mismos permisos `turnos.view`/`turnos.manage` que el
resto del módulo (ADR-029)."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.turnos.application.dtos.grilla_variante_dtos import (
    CreateGrillaVarianteCommand,
    UpdateGrillaVarianteCommand,
)
from src.modules.turnos.application.use_cases.cancel_grilla_variante import (
    CancelGrillaVariante,
)
from src.modules.turnos.application.use_cases.create_grilla_variante import (
    CreateGrillaVariante,
)
from src.modules.turnos.application.use_cases.grilla_variante_support import (
    GrillaVarianteDependencies,
)
from src.modules.turnos.application.use_cases.list_grilla_variantes import (
    ListGrillaVariantes,
)
from src.modules.turnos.application.use_cases.precargar_grilla_variante import (
    PrecargarGrillaVariante,
    PrecargarGrillaVarianteDependencies,
)
from src.modules.turnos.application.use_cases.update_grilla_variante import (
    UpdateGrillaVariante,
)
from src.modules.turnos.domain.well_known_permissions import MANAGE, VIEW
from src.modules.turnos.infrastructure.repositories.sqlalchemy_asignacion_repository import (
    SqlAlchemyAsignacionRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_ausencias_lookup import (
    SqlAlchemyAusenciasLookup,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_casilla_repository import (
    SqlAlchemyCasillaRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_grilla_variante_repository import (  # noqa: E501
    SqlAlchemyGrillaVarianteRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_slot_repository import (
    SqlAlchemySlotRepository,
)
from src.modules.turnos.infrastructure.repositories.sqlalchemy_user_provider import (
    SqlAlchemyUserProvider,
)
from src.modules.turnos.presentation.schemas.grilla_variante_schemas import (
    GrillaVarianteRequest,
    GrillaVarianteResponse,
    PrecargaGrillaResponse,
)
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.schemas.pagination import Page

router = APIRouter(prefix="/api/turnos/grilla-variantes", tags=["turnos"])

# Catálogo chico (un puñado de grillas por año) -- paginado por contrato
# (CLAUDE.md §11) con default generoso, igual que el resto de /api/turnos.
_DEFAULT_SIZE = 200
_require_view = Depends(require_permission(VIEW))
_require_manage = Depends(require_permission(MANAGE))


def _deps(db: AsyncSession) -> GrillaVarianteDependencies:
    return GrillaVarianteDependencies(
        variantes=SqlAlchemyGrillaVarianteRepository(db),
        casillas=SqlAlchemyCasillaRepository(db),
        slots=SqlAlchemySlotRepository(db),
        users=SqlAlchemyUserProvider(db),
        ausencias=SqlAlchemyAusenciasLookup(db),
    )


@router.get("")
async def list_grilla_variantes(
    vigentes: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=_DEFAULT_SIZE, ge=1, le=1000),
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> Page[GrillaVarianteResponse]:
    items = await ListGrillaVariantes(_deps(db)).execute(solo_vigentes=vigentes)
    return Page.of(
        [GrillaVarianteResponse.from_dto(i) for i in items], page=page, size=size
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_grilla_variante(
    payload: GrillaVarianteRequest,
    identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> GrillaVarianteResponse:
    dto = await CreateGrillaVariante(_deps(db)).execute(
        CreateGrillaVarianteCommand(
            motivo=payload.motivo,
            origen_texto=payload.origen_texto,
            desde=payload.desde,
            hasta=payload.hasta,
            slots=[s.to_input() for s in payload.slots],
            created_by_user_id=identity.user.id,
        )
    )
    return GrillaVarianteResponse.from_dto(dto)


@router.post("/precarga")
async def precargar_grilla_variante(
    ausente_user_id: uuid.UUID = Query(alias="ausenteUserId"),
    desde: date = Query(),
    hasta: date = Query(),
    _identity: Identity = _require_view,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> PrecargaGrillaResponse:
    """Solo lectura: no persiste nada. POST porque es una operación de cálculo
    con parámetros, no un recurso."""
    deps = PrecargarGrillaVarianteDependencies(
        base=_deps(db), asignaciones=SqlAlchemyAsignacionRepository(db)
    )
    dto = await PrecargarGrillaVariante(deps).execute(
        ausente_user_id=ausente_user_id, desde=desde, hasta=hasta
    )
    return PrecargaGrillaResponse.from_dto(dto)


@router.put("/{variante_id}")
async def update_grilla_variante(
    variante_id: uuid.UUID,
    payload: GrillaVarianteRequest,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> GrillaVarianteResponse:
    dto = await UpdateGrillaVariante(_deps(db)).execute(
        UpdateGrillaVarianteCommand(
            variante_id=variante_id,
            motivo=payload.motivo,
            origen_texto=payload.origen_texto,
            desde=payload.desde,
            hasta=payload.hasta,
            slots=[s.to_input() for s in payload.slots],
        )
    )
    return GrillaVarianteResponse.from_dto(dto)


@router.post("/{variante_id}/cancelar", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_grilla_variante(
    variante_id: uuid.UUID,
    _identity: Identity = _require_manage,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    await CancelGrillaVariante(_deps(db)).execute(variante_id)
