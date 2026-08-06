import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.value_objects.permission import Permission
from src.modules.auth.infrastructure.models.permission_models import PermissionAudit


class SqlAlchemyPermissionAuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_diff(
        self,
        *,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        added: frozenset[Permission],
        removed: frozenset[Permission],
    ) -> None:
        for permission in added:
            self._add_row(actor_user_id, target_user_id, permission, "grant")
        for permission in removed:
            self._add_row(actor_user_id, target_user_id, permission, "revoke")
        await self._session.flush()

    def _add_row(
        self,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        permission: Permission,
        operation: str,
    ) -> None:
        self._session.add(
            PermissionAudit(
                actor_user_id=actor_user_id,
                target_user_id=target_user_id,
                module_key=permission.module.value,
                action_key=permission.action.value,
                operation=operation,
            )
        )
