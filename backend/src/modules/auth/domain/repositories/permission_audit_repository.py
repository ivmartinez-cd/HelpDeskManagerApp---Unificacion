import uuid
from typing import Protocol

from src.shared.domain.value_objects.permission import Permission


class PermissionAuditRepository(Protocol):
    async def record_diff(
        self,
        *,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        added: frozenset[Permission],
        removed: frozenset[Permission],
    ) -> None: ...
