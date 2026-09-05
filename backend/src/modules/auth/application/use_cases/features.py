"""Funciones (pantallas/cards) por usuario (ADR-032): catálogo, lectura y
reemplazo atómico con auditoría -- espejo de los casos de uso de permisos."""

import uuid
from dataclasses import dataclass

from src.modules.auth.domain.errors import UnknownFeatureError, UserNotFoundError
from src.modules.auth.domain.repositories.feature_catalog_repository import (
    FeatureCatalogRepository,
)
from src.modules.auth.domain.repositories.feature_grant_repository import (
    FeatureGrantRepository,
)
from src.modules.auth.domain.repositories.permission_audit_repository import (
    PermissionAuditRepository,
)
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.value_objects.feature_catalog_entry import FeatureCatalogEntry
from src.modules.auth.domain.value_objects.feature_set import FeatureSet


@dataclass(frozen=True, slots=True)
class ListFeatureCatalogDependencies:
    catalog: FeatureCatalogRepository


class ListFeatureCatalog:
    def __init__(self, deps: ListFeatureCatalogDependencies) -> None:
        self._deps = deps

    async def execute(self) -> list[FeatureCatalogEntry]:
        return await self._deps.catalog.list_all()


@dataclass(frozen=True, slots=True)
class GetUserFeaturesDependencies:
    users: UserRepository
    features: FeatureGrantRepository


class GetUserFeatures:
    def __init__(self, deps: GetUserFeaturesDependencies) -> None:
        self._deps = deps

    async def execute(self, user_id: uuid.UUID) -> FeatureSet:
        if await self._deps.users.get_by_id(user_id) is None:
            raise UserNotFoundError()
        return await self._deps.features.get_for_user(user_id)


@dataclass(frozen=True, slots=True)
class ReplaceUserFeaturesDependencies:
    users: UserRepository
    features: FeatureGrantRepository
    catalog: FeatureCatalogRepository
    audit: PermissionAuditRepository


class ReplaceUserFeatures:
    """Reemplazo atómico e idempotente del set completo (mismo criterio que
    ReplaceUserPermissions): si no hay diff no escribe grants ni auditoría."""

    def __init__(self, deps: ReplaceUserFeaturesDependencies) -> None:
        self._deps = deps

    async def execute(
        self, *, target_user_id: uuid.UUID, desired: FeatureSet, actor_user_id: uuid.UUID
    ) -> None:
        if await self._deps.users.get_by_id(target_user_id) is None:
            raise UserNotFoundError()
        await self._ensure_in_catalog(desired)
        current = await self._deps.features.get_for_user(target_user_id)
        added = desired.granted - current.granted
        removed = current.granted - desired.granted
        if not added and not removed:
            return
        await self._deps.features.replace_for_user(
            target_user_id, desired, granted_by=actor_user_id
        )
        await self._deps.audit.record_feature_diff(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            added=added,
            removed=removed,
        )

    async def _ensure_in_catalog(self, desired: FeatureSet) -> None:
        # Validar antes de escribir: la FK a module_feature lo rechazaría
        # igual, pero como 500 y sin auditoría.
        valid = {entry.key for entry in await self._deps.catalog.list_all()}
        for key in sorted(desired.granted, key=lambda k: k.value):
            if key not in valid:
                raise UnknownFeatureError(key.value)
