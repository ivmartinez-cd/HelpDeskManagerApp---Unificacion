"""Límites del admin delegado (admin.manage sin superadmin) al editar permisos y
funciones: no se concede nada a sí mismo ni toca a otros administradores. Sin esto
admin.manage equivalía a superadmin (auditoría de seguridad 2026-09-30)."""

import uuid
from dataclasses import dataclass

from src.modules.auth.domain.errors import (
    AutoconcesionError,
    CuentaPrivilegiadaReservadaError,
    UserNotFoundError,
)
from src.modules.auth.domain.repositories.permission_repository import PermissionRepository
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.well_known_permissions import MANAGE_ADMIN


@dataclass(frozen=True, slots=True)
class EdicionDeAccesos:
    actor_user_id: uuid.UUID
    actor_is_superadmin: bool
    target_user_id: uuid.UUID
    agrega: bool


async def verificar_edicion_de_accesos(
    users: UserRepository, permissions: PermissionRepository, edicion: EdicionDeAccesos
) -> None:
    if edicion.actor_is_superadmin:
        return
    if edicion.target_user_id == edicion.actor_user_id:
        if edicion.agrega:
            raise AutoconcesionError()
        return
    if await _es_privilegiado(users, permissions, edicion.target_user_id):
        raise CuentaPrivilegiadaReservadaError()


async def _es_privilegiado(
    users: UserRepository, permissions: PermissionRepository, user_id: uuid.UUID
) -> bool:
    user = await users.get_by_id(user_id)
    if user is None:
        raise UserNotFoundError()
    if user.is_superadmin:
        return True
    return (await permissions.get_for_user(user_id)).allows(MANAGE_ADMIN)
