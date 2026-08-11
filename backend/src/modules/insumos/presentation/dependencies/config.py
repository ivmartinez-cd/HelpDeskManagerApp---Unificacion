"""Factories de la configuración del módulo (app_settings)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases.get_insumos_config import (
    GetInsumosConfig,
    GetInsumosConfigPorts,
)
from src.modules.insumos.application.use_cases.save_insumos_config import (
    SaveInsumosConfig,
    SaveInsumosConfigPorts,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
    SqlAlchemyInsumosSettingsRepository,
)


def build_get_insumos_config(session: AsyncSession) -> GetInsumosConfig:
    settings = SqlAlchemyInsumosSettingsRepository(session)
    return GetInsumosConfig(GetInsumosConfigPorts(settings=settings))


def build_save_insumos_config(session: AsyncSession) -> SaveInsumosConfig:
    settings = SqlAlchemyInsumosSettingsRepository(session)
    return SaveInsumosConfig(SaveInsumosConfigPorts(settings=settings))
