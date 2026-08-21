"""Endpoints de contactos de un PST — sub-router anidado bajo /api/prestadores
(lo incluye `prestadores_router`, que aporta el prefijo)."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.prestadores.application.dtos.prestador_dtos import UpsertContactoCommand
from src.modules.prestadores.application.use_cases.delete_contacto import (
    DeleteContacto,
    DeleteContactoDependencies,
)
from src.modules.prestadores.application.use_cases.upsert_contacto import (
    UpsertContacto,
    UpsertContactoDependencies,
)
from src.modules.prestadores.domain.well_known_permissions import CREATE, DELETE, UPDATE
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_contacto_repository import (
    SqlAlchemyContactoRepository,
)
from src.modules.prestadores.presentation.schemas.prestador_schemas import (
    ContactoResponse,
    UpsertContactoRequest,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter()

_require_create = Depends(require_permission(CREATE))
_require_update = Depends(require_permission(UPDATE))
_require_delete = Depends(require_permission(DELETE))


def _upsert_command(
    prestador_id: uuid.UUID, contacto_id: uuid.UUID | None, payload: UpsertContactoRequest
) -> UpsertContactoCommand:
    return UpsertContactoCommand(
        contacto_id=contacto_id,
        prestador_id=prestador_id,
        nombre=payload.nombre,
        telefono=payload.telefono,
        email=payload.email,
        is_principal=payload.is_principal,
        sort_order=payload.sort_order,
    )


@router.post("/{prestador_id}/contactos", status_code=status.HTTP_201_CREATED)
async def create_contacto(
    prestador_id: uuid.UUID,
    payload: UpsertContactoRequest,
    _: Identity = _require_create,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ContactoResponse:
    deps = UpsertContactoDependencies(contactos=SqlAlchemyContactoRepository(db))
    dto = await UpsertContacto(deps).execute(_upsert_command(prestador_id, None, payload))
    return ContactoResponse.from_dto(dto)


@router.put("/{prestador_id}/contactos/{contacto_id}")
async def update_contacto(
    prestador_id: uuid.UUID,
    contacto_id: uuid.UUID,
    payload: UpsertContactoRequest,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> ContactoResponse:
    deps = UpsertContactoDependencies(contactos=SqlAlchemyContactoRepository(db))
    dto = await UpsertContacto(deps).execute(_upsert_command(prestador_id, contacto_id, payload))
    return ContactoResponse.from_dto(dto)


@router.delete("/{prestador_id}/contactos/{contacto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contacto(
    prestador_id: uuid.UUID,
    contacto_id: uuid.UUID,
    _: Identity = _require_delete,
    db: AsyncSession = Depends(get_db, scope="function"),
) -> None:
    deps = DeleteContactoDependencies(contactos=SqlAlchemyContactoRepository(db))
    await DeleteContacto(deps).execute(contacto_id)
