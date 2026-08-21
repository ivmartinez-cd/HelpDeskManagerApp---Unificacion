import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.permission_models import PermissionAudit
from src.shared.domain.value_objects.feature_key import FeatureKey
from src.shared.domain.value_objects.permission import Permission

# Las funciones (ADR-032) comparten el log de permisos: module_key fijo y la
# clave de la función en action_key (ninguna de las dos columnas tiene FK).
_MODULE_FEATURE = "feature"


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

    async def record_feature_diff(
        self,
        *,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        added: frozenset[FeatureKey],
        removed: frozenset[FeatureKey],
    ) -> None:
        for key, operation in [(k, "grant") for k in added] + [(k, "revoke") for k in removed]:
            self._session.add(
                PermissionAudit(
                    actor_user_id=actor_user_id,
                    target_user_id=target_user_id,
                    module_key=_MODULE_FEATURE,
                    action_key=key.value,
                    operation=operation,
                )
            )
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
