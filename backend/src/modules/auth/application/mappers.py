import uuid

from src.modules.auth.application.dtos.results import Identity, PermissionView, UserView
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects.feature_set import FeatureSet
from src.modules.auth.domain.value_objects.permission_set import PermissionSet


def to_identity(
    user: User,
    permissions: PermissionSet,
    *,
    session_id: uuid.UUID,
    features: FeatureSet | None = None,
) -> Identity:
    return Identity(
        user=UserView(
            id=user.id,
            email=user.email.value,
            full_name=user.full_name,
            is_superadmin=user.is_superadmin,
            color=user.color,
        ),
        permissions=frozenset(
            PermissionView(module=p.module.value, action=p.action.value)
            for p in permissions.granted
        ),
        session_id=session_id,
        features=frozenset(f.value for f in (features or FeatureSet()).granted),
    )
