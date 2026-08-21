import uuid
from typing import Protocol

from src.modules.auth.domain.value_objects.feature_set import FeatureSet


class FeatureGrantRepository(Protocol):
    async def get_for_user(self, user_id: uuid.UUID) -> FeatureSet: ...
    async def replace_for_user(
        self, user_id: uuid.UUID, features: FeatureSet, *, granted_by: uuid.UUID
    ) -> None: ...


class FeatureGrantRepositoryNulo:
    """Default para wiring sin funciones (tests, scripts): nadie tiene ninguna."""

    async def get_for_user(self, user_id: uuid.UUID) -> FeatureSet:
        return FeatureSet()

    async def replace_for_user(
        self, user_id: uuid.UUID, features: FeatureSet, *, granted_by: uuid.UUID
    ) -> None:
        return None
