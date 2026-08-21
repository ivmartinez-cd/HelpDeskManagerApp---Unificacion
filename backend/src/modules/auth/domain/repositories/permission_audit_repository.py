import uuid
from typing import Protocol

from src.shared.domain.value_objects.feature_key import FeatureKey
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

    async def record_feature_diff(
        self,
        *,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        added: frozenset[FeatureKey],
        removed: frozenset[FeatureKey],
    ) -> None:
        """Mismo log que los permisos (permission_audit) con
        module_key='feature' y action_key=<clave de la función>."""
        ...
