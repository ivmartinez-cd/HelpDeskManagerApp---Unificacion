import uuid
from dataclasses import dataclass

from src.modules.auth.domain.repositories.permission_repository import PermissionRepository
from src.modules.auth.domain.value_objects.permission_set import PermissionSet


@dataclass(frozen=True, slots=True)
class GetUserPermissionsDependencies:
    permissions: PermissionRepository


class GetUserPermissions:
    def __init__(self, deps: GetUserPermissionsDependencies) -> None:
        self._deps = deps

    async def execute(self, user_id: uuid.UUID) -> PermissionSet:
        return await self._deps.permissions.get_for_user(user_id)
