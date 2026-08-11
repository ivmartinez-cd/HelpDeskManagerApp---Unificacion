"""Factories de los dos casos de uso de estadísticas."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases.get_customer_statistics import (
    GetCustomerStatistics,
    GetCustomerStatisticsPorts,
)
from src.modules.insumos.application.use_cases.get_statistics_overview import (
    GetStatisticsOverview,
    GetStatisticsOverviewPorts,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_audit_statistics_repository import (  # noqa: E501
    SqlAlchemyAuditStatisticsRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_customer_config_repository import (  # noqa: E501
    SqlAlchemyCustomerConfigRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
    SqlAlchemyInsumosSettingsRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_known_device_repository import (  # noqa: E501
    SqlAlchemyKnownDeviceRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_supply_cache_repository import (
    SqlAlchemySupplyCacheRepository,
)
from src.modules.insumos.presentation.wiring import app_timezone


def build_get_statistics_overview(session: AsyncSession) -> GetStatisticsOverview:
    ports = GetStatisticsOverviewPorts(stats=SqlAlchemyAuditStatisticsRepository(session))
    return GetStatisticsOverview(ports, app_timezone())


def build_get_customer_statistics(session: AsyncSession) -> GetCustomerStatistics:
    ports = GetCustomerStatisticsPorts(
        stats=SqlAlchemyAuditStatisticsRepository(session),
        customers=SqlAlchemyCustomerConfigRepository(session),
        devices=SqlAlchemyKnownDeviceRepository(session),
        supply_cache=SqlAlchemySupplyCacheRepository(session),
        settings=SqlAlchemyInsumosSettingsRepository(session),
    )
    return GetCustomerStatistics(ports, app_timezone())
