"""Factories de las alertas de solicitudes sin cargar."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases.list_alerts import (
    AcknowledgeAlerts,
    AlertsPorts,
    ListAlerts,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
    SqlAlchemyInsumosSettingsRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_request_alert_repository import (  # noqa: E501
    SqlAlchemyRequestAlertRepository,
)
from src.modules.insumos.presentation.wiring import app_timezone


def _ports(session: AsyncSession) -> AlertsPorts:
    return AlertsPorts(
        alerts=SqlAlchemyRequestAlertRepository(session),
        settings=SqlAlchemyInsumosSettingsRepository(session),
    )


def build_list_alerts(session: AsyncSession) -> ListAlerts:
    return ListAlerts(_ports(session), app_timezone())


def build_acknowledge_alerts(session: AsyncSession) -> AcknowledgeAlerts:
    return AcknowledgeAlerts(_ports(session))
