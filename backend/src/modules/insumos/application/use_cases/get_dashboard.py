"""Caso de uso GetDashboard — port de compute_dashboard_state (pending_requests.py).

Las 4 fases del legacy, en async:
1. Por cliente habilitado: solicitudes OUTSTANDING (sin stale) + ids procesados + series
   de los equipos — errores por cliente aislados (el dashboard nunca cae entero).
   Ver `_dashboard_customer_fetch.py`.
2. Un único refresh SOAP global de estados de pedidos procesados (con TTL de cache).
3. Liberar solicitudes cuyo pedido quedó Anulado/Cancelado en CD (audit RELEASED).
   Fases 2 y 3 en `_dashboard_release.py`.
4. Agregación pura por cliente (domain/services/dashboard_summary).

Las fases 1-3 viven en archivos aparte porque juntas superaban el tamaño máximo de
archivo (§4) — GetDashboardPorts se queda acá porque lo reusan `list_requests.py` y
`_request_association.py`.

Pendiente explícito: el TTLCache de equipos del legacy (device_cache) se porta junto con
el poller — hasta entonces cada carga consulta los equipos en vivo; y pending_list (el
insumo del job de alertas) llega con el port del módulo de alertas.
"""

import asyncio
from dataclasses import dataclass

from src.modules.insumos.application.dtos.dashboard import DashboardResult, DashboardThresholds
from src.modules.insumos.application.use_cases._dashboard_customer_fetch import (
    CustomerFetch,
    fetch_customer,
)
from src.modules.insumos.application.use_cases._dashboard_release import ReleaseReconciler
from src.modules.insumos.domain.repositories.customer_config_repository import (
    CustomerConfigRepository,
)
from src.modules.insumos.domain.repositories.insight_gateway import InsightGateway
from src.modules.insumos.domain.repositories.insumos_settings_repository import (
    InsumosSettingsRepository,
)
from src.modules.insumos.domain.repositories.order_audit_repository import OrderAuditRepository
from src.modules.insumos.domain.repositories.processed_request_repository import (
    ProcessedRequestRepository,
)
from src.modules.insumos.domain.repositories.supply_cache_repository import SupplyCacheRepository
from src.modules.insumos.domain.repositories.wsayc_gateway import WsAycGateway
from src.modules.insumos.domain.services.dashboard_summary import (
    CustomerRequests,
    CustomerSummary,
    summarize_customers,
)
from src.modules.insumos.domain.value_objects.insumos_settings import (
    InsumosSettings,
    settings_from_raw,
)


@dataclass(frozen=True)
class GetDashboardPorts:
    insight: InsightGateway
    wsayc: WsAycGateway
    processed: ProcessedRequestRepository
    supply_cache: SupplyCacheRepository
    customers: CustomerConfigRepository
    settings: InsumosSettingsRepository
    audit: OrderAuditRepository


class GetDashboard:
    def __init__(self, ports: GetDashboardPorts) -> None:
        self._ports = ports

    async def execute(self, refresh_minutes: int) -> DashboardResult:
        settings = settings_from_raw(await self._ports.settings.get_all())
        customers = await self._ports.customers.list_enabled()
        fetches: list[CustomerFetch] = list(
            await asyncio.gather(
                *(
                    fetch_customer(
                        self._ports.insight, self._ports.processed, c.customer_id, c.name
                    )
                    for c in customers
                )
            )
        )
        released = await ReleaseReconciler(
            self._ports.wsayc, self._ports.processed, self._ports.supply_cache, self._ports.audit
        ).execute(fetches)
        datas = [_without_released(f.data, released) for f in fetches]
        per_customer, totals = await self._summarize(datas, settings)
        return DashboardResult(
            totals=totals,
            loaded_today=await self._ports.processed.count_processed_today(),
            customers_enabled=len(customers),
            per_customer=per_customer,
            thresholds=DashboardThresholds(
                critical=settings.threshold_critical,
                urgent=settings.threshold_urgent,
                warning=settings.threshold_warning,
            ),
            refresh_minutes=refresh_minutes,
        )

    async def _summarize(
        self, datas: list[CustomerRequests], settings: InsumosSettings
    ) -> tuple[list[CustomerSummary], dict[str, int]]:
        pending_serials = sorted(
            {
                s.device_serial
                for data in datas
                for s in data.requests
                if s.hp_request_id not in data.processed_ids and s.device_serial
            }
        )
        supplies = await self._ports.supply_cache.get_noncancelled_by_serials(pending_serials)
        own_orders = await self._ports.processed.get_created_by_serials(pending_serials)
        return summarize_customers(datas, settings, supplies, own_orders)


def _without_released(data: CustomerRequests, released: set[int]) -> CustomerRequests:
    """Las solicitudes liberadas en fase 3 vuelven a contar como pendientes."""
    if not released & set(data.processed_ids):
        return data
    return CustomerRequests(
        customer_id=data.customer_id,
        name=data.name,
        requests=data.requests,
        processed_ids=frozenset(data.processed_ids - released),
        error=data.error,
    )
