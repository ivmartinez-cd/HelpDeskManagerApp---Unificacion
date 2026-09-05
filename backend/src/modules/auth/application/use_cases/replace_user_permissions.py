import uuid
from dataclasses import dataclass

from src.modules.auth.domain.errors import (
    AdminManageReservedError,
    CannotDemoteSelfError,
    UnknownPermissionError,
    UserNotFoundError,
)
from src.modules.auth.domain.repositories.module_catalog_repository import (
    ModuleCatalogRepository,
)
from src.modules.auth.domain.repositories.permission_audit_repository import (
    PermissionAuditRepository,
)
from src.modules.auth.domain.repositories.permission_repository import PermissionRepository
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.value_objects.permission_set import PermissionSet
from src.modules.auth.domain.well_known_permissions import MANAGE_ADMIN
from src.shared.domain.value_objects.permission import Permission


@dataclass(frozen=True, slots=True)
class ReplaceUserPermissionsDependencies:
    users: UserRepository
    permissions: PermissionRepository
    catalog: ModuleCatalogRepository
    audit: PermissionAuditRepository


class ReplaceUserPermissions:
    """Reemplazo atómico del estado deseado completo. Idempotente por
    diseño: si `desired` coincide con lo que ya hay, no escribe nada — ni
    en permission_grant ni en permission_audit (sin eso, repetir el mismo
    PUT generaría filas de auditoría fantasma cada vez)."""

    def __init__(self, deps: ReplaceUserPermissionsDependencies) -> None:
        self._deps = deps

    async def execute(
        self,
        *,
        target_user_id: uuid.UUID,
        desired: PermissionSet,
        actor_user_id: uuid.UUID,
        actor_is_superadmin: bool = False,
    ) -> None:
        if target_user_id == actor_user_id and not desired.allows(MANAGE_ADMIN):
            raise CannotDemoteSelfError()
        await self._ensure_target_and_catalog(target_user_id, desired)
        current = await self._deps.permissions.get_for_user(target_user_id)
        added = desired.granted - current.granted
        removed = current.granted - desired.granted
        if not added and not removed:
            return
        if MANAGE_ADMIN in added | removed and not actor_is_superadmin:
            raise AdminManageReservedError()
        await self._persist(target_user_id, desired, actor_user_id, added, removed)

    async def _persist(
        self,
        target_user_id: uuid.UUID,
        desired: PermissionSet,
        actor_user_id: uuid.UUID,
        added: frozenset[Permission],
        removed: frozenset[Permission],
    ) -> None:
        await self._deps.permissions.replace_for_user(
            target_user_id, desired, granted_by=actor_user_id
        )
        await self._deps.audit.record_diff(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            added=added,
            removed=removed,
        )

    async def _ensure_target_and_catalog(
        self, target_user_id: uuid.UUID, desired: PermissionSet
    ) -> None:
        # Validar antes de escribir: las FKs de permission_grant (usuario y
        # module_action) lo rechazarían igual, pero como 500 y sin auditoría.
        if await self._deps.users.get_by_id(target_user_id) is None:
            raise UserNotFoundError()
        valid = {
            Permission(entry.key, action)
            for entry in await self._deps.catalog.list_all()
            for action in entry.actions
        }
        for permission in sorted(desired.granted, key=lambda p: (p.module.value, p.action.value)):
            if permission not in valid:
                raise UnknownPermissionError(permission.module.value, permission.action.value)
