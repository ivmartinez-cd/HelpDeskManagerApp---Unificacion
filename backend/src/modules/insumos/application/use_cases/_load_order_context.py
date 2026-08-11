"""Dependencias y config del caso de uso LoadOrder, agrupadas (guía §4: más de 3
parámetros se agrupan en un objeto)."""

from dataclasses import dataclass

from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)
from src.modules.insumos.domain.repositories.request_validation_repository import (
    RequestValidationRepository,
)
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.zone_contact_repository import ZoneContactRepository
from src.modules.insumos.domain.services.claimed_order_creation import ClaimedOrderCreation
from src.modules.insumos.domain.services.order_creation import CanalDirectoOrderCreation
from src.modules.insumos.domain.services.supply_request_matching import SupplyMatchResolver
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings


@dataclass(frozen=True)
class LoadOrderPorts:
    insight: InsightGateway
    processed: ProcessedRequestRepository
    audit: OrderAuditRepository
    validations: RequestValidationRepository
    zone_contacts: ZoneContactRepository
    supply_cache: SupplyCacheRepository
    claimed_creation: ClaimedOrderCreation
    order_creation: CanalDirectoOrderCreation
    match_resolver: SupplyMatchResolver


@dataclass(frozen=True)
class LoadOrderConfig:
    order_settings: CanalDirectoOrderSettings
    timezone: str = "America/Argentina/Buenos_Aires"
    # INSIGHT_MARK_ACTIONED / INSIGHT_STATUS_ON_ORDER del legacy — nótese ACTION,
    # no ACTIONED (bug corregido documentado en el CHANGELOG legacy [1.0.0]).
    insight_mark_actioned: bool = False
    insight_status_on_order: str = "ACTION"
