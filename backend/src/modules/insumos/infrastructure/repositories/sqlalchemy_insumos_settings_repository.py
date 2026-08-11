"""Implementación Postgres del puerto InsumosSettingsRepository (app_settings k-v)."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.infrastructure.models.app_setting_model import AppSettingModel


class SqlAlchemyInsumosSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> dict[str, str]:
        rows = (await self._session.execute(select(AppSettingModel))).scalars().all()
        return {row.key: row.value for row in rows}

    async def set_all(self, values: dict[str, str]) -> None:
        if not values:
            return
        stmt = insert(AppSettingModel).values(
            [{"key": key, "value": value} for key, value in values.items()]
        )
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=[AppSettingModel.key],
                set_={"value": stmt.excluded.value},
            )
        )
