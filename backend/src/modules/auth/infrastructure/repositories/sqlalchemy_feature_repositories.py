"""Catálogo de funciones y grants por usuario (ADR-032)."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.value_objects.feature_catalog_entry import FeatureCatalogEntry
from src.modules.auth.domain.value_objects.feature_set import FeatureSet
from src.modules.auth.infrastructure.models.permission_models import (
    ModuleFeature,
    UserFeatureGrant,
)
from src.shared.domain.value_objects.feature_key import FeatureKey
from src.shared.domain.value_objects.module_key import ModuleKey


class SqlAlchemyFeatureCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[FeatureCatalogEntry]:
        stmt = select(ModuleFeature).order_by(ModuleFeature.module_key, ModuleFeature.sort_order)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            FeatureCatalogEntry(
                key=FeatureKey(row.key),
                module=ModuleKey(row.module_key),
                label=row.label,
                description=row.description,
                sort_order=row.sort_order,
            )
            for row in rows
        ]


class SqlAlchemyFeatureGrantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_user(self, user_id: uuid.UUID) -> FeatureSet:
        stmt = select(UserFeatureGrant.feature_key).where(UserFeatureGrant.user_id == user_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return FeatureSet(frozenset(FeatureKey(k) for k in rows))

    async def replace_for_user(
        self, user_id: uuid.UUID, features: FeatureSet, *, granted_by: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(UserFeatureGrant).where(UserFeatureGrant.user_id == user_id)
        )
        for key in features.granted:
            self._session.add(
                UserFeatureGrant(user_id=user_id, feature_key=key.value, granted_by=granted_by)
            )
        await self._session.flush()
