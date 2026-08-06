import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.value_objects.action_key import ActionKey
from src.modules.auth.domain.value_objects.module_key import ModuleKey
from src.modules.auth.domain.value_objects.permission import Permission
from src.modules.auth.domain.value_objects.permission_set import PermissionSet
from src.modules.auth.infrastructure.models.permission_models import PermissionGrant


class SqlAlchemyPermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_user(self, user_id: uuid.UUID) -> PermissionSet:
        stmt = select(PermissionGrant.module_key, PermissionGrant.action_key).where(
            PermissionGrant.user_id == user_id
        )
        rows = (await self._session.execute(stmt)).all()
        granted = frozenset(Permission(ModuleKey(m), ActionKey(a)) for m, a in rows)
        return PermissionSet(granted)

    async def replace_for_user(
        self, user_id: uuid.UUID, permissions: PermissionSet, *, granted_by: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(PermissionGrant).where(PermissionGrant.user_id == user_id)
        )
        for permission in permissions.granted:
            self._session.add(
                PermissionGrant(
                    user_id=user_id,
                    module_key=permission.module.value,
                    action_key=permission.action.value,
                    granted_by=granted_by,
                )
            )
        await self._session.flush()
