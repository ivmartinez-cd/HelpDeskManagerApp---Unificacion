"""Wiring del módulo insumos: singletons de gateways externos + armado de LoadOrder.

Los gateways son singletons de proceso a propósito: ZeepWsAycGateway cachea el cliente
zeep (cargar el WSDL es caro) y HttpxInsightGateway cachea el token con su margen de
refresco — recrearlos por request tiraría ambos caches.
"""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases._load_order_context import (
    LoadOrderConfig,
    LoadOrderPorts,
)
from src.modules.insumos.application.use_cases.cancel_order import CancelOrder, CancelOrderPorts
from src.modules.insumos.application.use_cases.dismiss_request import (
    DismissRequest,
    DismissRequestPorts,
)
from src.modules.insumos.application.use_cases.get_availability_windows import (
    GetAvailabilityWindows,
)
from src.modules.insumos.application.use_cases.get_consumable_detail import GetConsumableDetail
from src.modules.insumos.application.use_cases.get_consumable_history import (
    GetConsumableHistory,
)
from src.modules.insumos.application.use_cases.get_consumable_request_history import (
    GetConsumableRequestHistory,
)
from src.modules.insumos.application.use_cases.get_dashboard import (
    GetDashboard,
    GetDashboardPorts,
)
from src.modules.insumos.application.use_cases.get_device_supplies import (
    GetDeviceSupplies,
    GetDeviceSuppliesPorts,
)
from src.modules.insumos.application.use_cases.list_audit import ListAudit, ListAuditPorts
from src.modules.insumos.application.use_cases.list_requests import (
    ListRequests,
    ListRequestsConfig,
    ListRequestsPorts,
)
from src.modules.insumos.application.use_cases.load_order import LoadOrder
from src.modules.insumos.application.use_cases.reconcile_order import (
    ReconcileOrder,
    ReconcileOrderConfig,
    ReconcileOrderPorts,
)
from src.modules.insumos.application.use_cases.validation_window import (
    ValidationWindow,
    ValidationWindowPorts,
)
from src.modules.insumos.domain.services.claimed_order_creation import ClaimedOrderCreation
from src.modules.insumos.domain.services.order_creation import CanalDirectoOrderCreation
from src.modules.insumos.domain.services.supply_lookup import CanalDirectoSupplyLookup
from src.modules.insumos.domain.services.supply_request_matching import SupplyMatchResolver
from src.modules.insumos.domain.services.validation_diagnosis import ValidationDiagnosis
from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.modules.insumos.infrastructure.insight.httpx_insight_gateway import HttpxInsightGateway
from src.modules.insumos.infrastructure.repositories.sqlalchemy_customer_config_repository import (  # noqa: E501
    SqlAlchemyCustomerConfigRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
    SqlAlchemyInsumosSettingsRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_order_audit_repository import (
    SqlAlchemyOrderAuditRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_order_claim_repository import (
    SqlAlchemyOrderClaimRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_processed_request_repository import (  # noqa: E501
    SqlAlchemyProcessedRequestRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_request_validation_repository import (  # noqa: E501
    SqlAlchemyRequestValidationRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_supply_cache_repository import (
    SqlAlchemySupplyCacheRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_zone_contact_repository import (
    SqlAlchemyZoneContactRepository,
)
from src.modules.insumos.infrastructure.soap.zeep_wsayc_gateway import ZeepWsAycGateway
from src.shared.infrastructure.config.settings import Settings, get_settings


@lru_cache
def get_wsayc_gateway() -> ZeepWsAycGateway:
    return ZeepWsAycGateway()


@lru_cache
def get_insight_gateway() -> HttpxInsightGateway:
    settings = get_settings()
    return HttpxInsightGateway(
        settings.insight_base_url,
        settings.insight_api_key,
        settings.insight_api_secret.get_secret_value(),
    )


def _order_settings(settings: Settings) -> CanalDirectoOrderSettings:
    return CanalDirectoOrderSettings(
        solicitante=ContactInfo(
            apellido=settings.cd_solicitante_apellido,
            nombre=settings.cd_solicitante_nombre,
            telefono=settings.cd_solicitante_telefono,
            email=settings.cd_solicitante_email,
            sector=settings.cd_solicitante_sector,
        ),
        destinatario=ContactInfo(
            apellido=settings.cd_destinatario_apellido,
            nombre=settings.cd_destinatario_nombre,
            telefono=settings.cd_destinatario_telefono,
            email=settings.cd_destinatario_email,
            sector=settings.cd_destinatario_sector,
        ),
        origen_id=settings.cd_origen_id,
        motivo_id=settings.cd_motivo_id,
        portal_base_url=settings.cd_base_url,
    )


def build_get_dashboard(session: AsyncSession) -> GetDashboard:
    supply_cache = SqlAlchemySupplyCacheRepository(session)
    ports = GetDashboardPorts(
        insight=get_insight_gateway(),
        wsayc=get_wsayc_gateway(),
        processed=SqlAlchemyProcessedRequestRepository(session),
        supply_cache=supply_cache,
        customers=SqlAlchemyCustomerConfigRepository(session),
        settings=SqlAlchemyInsumosSettingsRepository(session),
        audit=SqlAlchemyOrderAuditRepository(session),
    )
    return GetDashboard(ports)


def build_list_requests(session: AsyncSession) -> ListRequests:
    settings = get_settings()
    wsayc = get_wsayc_gateway()
    supply_cache = SqlAlchemySupplyCacheRepository(session)
    order_settings = _order_settings(settings)
    dashboard_ports = GetDashboardPorts(
        insight=get_insight_gateway(),
        wsayc=wsayc,
        processed=SqlAlchemyProcessedRequestRepository(session),
        supply_cache=supply_cache,
        customers=SqlAlchemyCustomerConfigRepository(session),
        settings=SqlAlchemyInsumosSettingsRepository(session),
        audit=SqlAlchemyOrderAuditRepository(session),
    )
    insight = get_insight_gateway()
    validations = SqlAlchemyRequestValidationRepository(session)
    ports = ListRequestsPorts(
        dashboard=dashboard_ports,
        validations=validations,
        supply_lookup=CanalDirectoSupplyLookup(wsayc, supply_cache, order_settings),
        validation_window=ValidationWindow(
            ValidationWindowPorts(
                insight=insight,
                validations=validations,
                audit=SqlAlchemyOrderAuditRepository(session),
                diagnosis=ValidationDiagnosis(insight, wsayc),
            )
        ),
    )
    config = ListRequestsConfig(
        order_settings=order_settings, insight_base_url=settings.insight_base_url
    )
    return ListRequests(ports, config)


def build_load_order(session: AsyncSession) -> LoadOrder:
    settings = get_settings()
    wsayc = get_wsayc_gateway()
    supply_cache = SqlAlchemySupplyCacheRepository(session)
    order_settings = _order_settings(settings)
    ports = LoadOrderPorts(
        insight=get_insight_gateway(),
        processed=SqlAlchemyProcessedRequestRepository(session),
        audit=SqlAlchemyOrderAuditRepository(session),
        validations=SqlAlchemyRequestValidationRepository(session),
        zone_contacts=SqlAlchemyZoneContactRepository(session),
        supply_cache=supply_cache,
        claimed_creation=ClaimedOrderCreation(SqlAlchemyOrderClaimRepository(session)),
        order_creation=CanalDirectoOrderCreation(wsayc, supply_cache, order_settings),
        match_resolver=SupplyMatchResolver(wsayc, supply_cache),
    )
    config = LoadOrderConfig(
        order_settings=order_settings,
        timezone=settings.app_timezone,
        insight_mark_actioned=settings.insight_mark_actioned,
        insight_status_on_order=settings.insight_status_on_order,
    )
    return LoadOrder(ports, config)


def build_list_audit(session: AsyncSession) -> ListAudit:
    ports = ListAuditPorts(
        audit=SqlAlchemyOrderAuditRepository(session),
        insight=get_insight_gateway(),
    )
    return ListAudit(ports, _order_settings(get_settings()))


def build_cancel_order(session: AsyncSession) -> CancelOrder:
    return CancelOrder(
        CancelOrderPorts(
            wsayc=get_wsayc_gateway(),
            processed=SqlAlchemyProcessedRequestRepository(session),
            supply_cache=SqlAlchemySupplyCacheRepository(session),
            audit=SqlAlchemyOrderAuditRepository(session),
        )
    )


def build_dismiss_request(session: AsyncSession) -> DismissRequest:
    return DismissRequest(
        DismissRequestPorts(
            insight=get_insight_gateway(),
            processed=SqlAlchemyProcessedRequestRepository(session),
            audit=SqlAlchemyOrderAuditRepository(session),
        )
    )


def build_get_device_supplies(session: AsyncSession) -> GetDeviceSupplies:
    ports = GetDeviceSuppliesPorts(
        wsayc=get_wsayc_gateway(),
        supply_cache=SqlAlchemySupplyCacheRepository(session),
        processed=SqlAlchemyProcessedRequestRepository(session),
    )
    return GetDeviceSupplies(ports, _order_settings(get_settings()))


def build_get_consumable_history() -> GetConsumableHistory:
    return GetConsumableHistory(get_insight_gateway())


def build_get_consumable_request_history() -> GetConsumableRequestHistory:
    return GetConsumableRequestHistory(get_insight_gateway())


def build_get_availability_windows() -> GetAvailabilityWindows:
    return GetAvailabilityWindows(get_insight_gateway())


def build_get_consumable_detail() -> GetConsumableDetail:
    return GetConsumableDetail(get_insight_gateway())


def build_reconcile_order(session: AsyncSession) -> ReconcileOrder:
    settings = get_settings()
    wsayc = get_wsayc_gateway()
    order_settings = _order_settings(settings)
    ports = ReconcileOrderPorts(
        insight=get_insight_gateway(),
        processed=SqlAlchemyProcessedRequestRepository(session),
        audit=SqlAlchemyOrderAuditRepository(session),
        supply_lookup=CanalDirectoSupplyLookup(
            wsayc, SqlAlchemySupplyCacheRepository(session), order_settings
        ),
        claimed_creation=ClaimedOrderCreation(SqlAlchemyOrderClaimRepository(session)),
    )
    config = ReconcileOrderConfig(
        order_settings=order_settings,
        insight_mark_actioned=settings.insight_mark_actioned,
        insight_status_on_order=settings.insight_status_on_order,
    )
    return ReconcileOrder(ports, config)
