import uuid
from typing import Protocol

from src.modules.auth.domain.value_objects.permission_set import PermissionSet


class PermissionRepository(Protocol):
    async def get_for_user(self, user_id: uuid.UUID) -> PermissionSet: ...
    async def replace_for_user(
        self, user_id: uuid.UUID, permissions: PermissionSet, *, granted_by: uuid.UUID
    ) -> None: ...
