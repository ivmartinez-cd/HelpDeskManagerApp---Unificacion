import uuid
from dataclasses import dataclass

from src.modules.auth.domain.errors import CannotDemoteSelfError
from src.modules.auth.domain.repositories.permission_audit_repository import (
    PermissionAuditRepository,
)
from src.modules.auth.domain.repositories.permission_repository import PermissionRepository
from src.modules.auth.domain.value_objects.permission_set import PermissionSet
from src.modules.auth.domain.well_known_permissions import MANAGE_ADMIN


@dataclass(frozen=True, slots=True)
class ReplaceUserPermissionsDependencies:
    permissions: PermissionRepository
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
    ) -> None:
        if target_user_id == actor_user_id and not desired.allows(MANAGE_ADMIN):
            raise CannotDemoteSelfError()
        current = await self._deps.permissions.get_for_user(target_user_id)
        added = desired.granted - current.granted
        removed = current.granted - desired.granted
        if not added and not removed:
            return
        await self._deps.permissions.replace_for_user(
            target_user_id, desired, granted_by=actor_user_id
        )
        await self._deps.audit.record_diff(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            added=added,
            removed=removed,
        )
