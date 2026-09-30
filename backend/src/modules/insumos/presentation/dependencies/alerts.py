"""Factories de las alertas de solicitudes sin cargar."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases.list_alerts import (
    AcknowledgeAlerts,
    AlertsPorts,
    ListAlerts,
)
from src.modules.insumos.application.use_cases.sync_pending_alerts import (
    SyncPendingAlerts,
    SyncPendingAlertsPorts,
)
from src.modules.insumos.domain.repositories.request_alert_repository import (
    RequestAlertRepository,
)
from src.modules.insumos.infrastructure.repositories.request_alerts_con_aviso import (
    RequestAlertsConAviso,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_customer_config_repository import (  # noqa: E501
    SqlAlchemyCustomerConfigRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
    SqlAlchemyInsumosSettingsRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_processed_request_repository import (  # noqa: E501
    SqlAlchemyProcessedRequestRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_request_alert_repository import (  # noqa: E501
    SqlAlchemyRequestAlertRepository,
)
from src.modules.insumos.presentation.wiring import app_timezone, get_insight_gateway
from src.modules.notificaciones.infrastructure.repositories.sqlalchemy_notificacion_repository import (  # noqa: E501
    SqlAlchemyNotificacionRepository,
)


def _alertas(session: AsyncSession) -> RequestAlertRepository:
    """Alertas que, al escalar, avisan en la campanita (ADR-041), en la misma
    sesión que la escalada."""
    return RequestAlertsConAviso(
        SqlAlchemyRequestAlertRepository(session), SqlAlchemyNotificacionRepository(session)
    )


def _ports(session: AsyncSession) -> AlertsPorts:
    return AlertsPorts(
        alerts=_alertas(session),
        settings=SqlAlchemyInsumosSettingsRepository(session),
    )


def build_list_alerts(session: AsyncSession) -> ListAlerts:
    return ListAlerts(_ports(session), app_timezone())


def build_acknowledge_alerts(session: AsyncSession) -> AcknowledgeAlerts:
    return AcknowledgeAlerts(_ports(session))


def build_sync_pending_alerts(session: AsyncSession) -> SyncPendingAlerts:
    ports = SyncPendingAlertsPorts(
        insight=get_insight_gateway(),
        customers=SqlAlchemyCustomerConfigRepository(session),
        processed=SqlAlchemyProcessedRequestRepository(session),
        alerts=_alertas(session),
        settings=SqlAlchemyInsumosSettingsRepository(session),
    )
    return SyncPendingAlerts(ports, app_timezone())
