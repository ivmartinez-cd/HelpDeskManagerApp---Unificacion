"""Implementación Postgres del puerto InsumosSettingsRepository (app_settings k-v)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.infrastructure.models.app_setting_model import AppSettingModel


class SqlAlchemyInsumosSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> dict[str, str]:
        rows = (await self._session.execute(select(AppSettingModel))).scalars().all()
        return {row.key: row.value for row in rows}
