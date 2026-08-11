"""Caso de uso GetCustomerStatistics — port de GET /api/estadisticas/clientes/{id}.

Drill-down del overview: éxito/error, tiempo de atención, tránsito logístico,
consumibles y equipos más pedidos, y comparativa contra el período anterior.

Desviación consciente del legacy: `distinct_skus` sale del ranking COMPLETO de SKUs
del cliente, no de los 10 que se muestran. El legacy pedía el ranking ya limitado a
10 y contaba ese largo, así que "SKUs distintos" nunca podía pasar de 10 — un techo
que no era intencional (el overview sí pedía 1000 para contar y recortaba después).
"""

from dataclasses import dataclass
from datetime import date, datetime, tzinfo

from src.modules.insumos.application.dtos.statistics import CustomerStatistics
from src.modules.insumos.application.use_cases._customer_elapsed_stats import (
    ElapsedPair,
    to_fulfillment_stats,
    to_pending_to_dispatch_stats,
)
from src.modules.insumos.application.use_cases._customer_statistics_data import (
    CustomerAggregates,
    gather_customer_aggregates,
)
from src.modules.insumos.domain.entities.audit_record import EVENT_CREATED, EVENT_FAILED
from src.modules.insumos.domain.repositories.audit_statistics_repository import (
    AuditStatisticsRepository,
)
from src.modules.insumos.domain.repositories.customer_config_repository import (
    CustomerConfigRepository,
)
from src.modules.insumos.domain.repositories.insumos_settings_repository import (
    InsumosSettingsRepository,
)
from src.modules.insumos.domain.repositories.known_device_repository import (
    KnownDeviceRepository,
)
from src.modules.insumos.domain.repositories.supply_cache_repository import (
    SupplyCacheRepository,
)
from src.modules.insumos.domain.services.fulfillment_stats import (
    compute_fulfillment,
    compute_pending_to_dispatch,
    supply_id_of,
)
from src.modules.insumos.domain.services.statistics_series import peak_of
from src.modules.insumos.domain.value_objects.insumos_settings import settings_from_raw
from src.modules.insumos.domain.value_objects.stats_range import (
    StatsRange,
    resolve_stats_range,
)
from src.shared.domain.errors import NotFoundError

TOP_SKUS_LIMIT = 10


@dataclass(frozen=True)
class GetCustomerStatisticsPorts:
    stats: AuditStatisticsRepository
    customers: CustomerConfigRepository
    devices: KnownDeviceRepository
    supply_cache: SupplyCacheRepository
    settings: InsumosSettingsRepository


class GetCustomerStatistics:
    def __init__(self, ports: GetCustomerStatisticsPorts, timezone: tzinfo) -> None:
        self._ports = ports
        # El horario laboral del tiempo de atención se mide en hora local, igual que
        # el "hoy" del rango — nunca en la hora UTC del contenedor.
        self._timezone = timezone

    async def execute(
        self,
        customer_id: int,
        days: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> CustomerStatistics:
        period = resolve_stats_range(
            days, start_date, end_date, today=datetime.now(self._timezone).date()
        )
        name = await self._resolve_name(customer_id)
        data = await gather_customer_aggregates(
            self._ports.stats, self._ports.devices, customer_id, period
        )
        elapsed = await self._elapsed(data)
        return _build(customer_id, name, period, data, elapsed)

    async def _resolve_name(self, customer_id: int) -> str:
        """Padrón primero; si el cliente se podó del padrón pero todavía tiene
        historial, el último nombre visto en order_audit. Sin ninguno, no existe."""
        name = (await self._ports.customers.get_names()).get(customer_id)
        name = name or await self._ports.stats.customer_name(customer_id)
        if not name:
            raise NotFoundError(f"No existe el cliente {customer_id}")
        return name

    async def _elapsed(self, data: CustomerAggregates) -> ElapsedPair:
        settings = settings_from_raw(await self._ports.settings.get_all())
        total_created = data.current.get(EVENT_CREATED, 0)
        history = await self._ports.supply_cache.get_status_history_batch(
            _supply_ids_of(data)
        )
        fulfillment = compute_fulfillment(
            data.fulfillment_rows,
            timezone=self._timezone,
            work_hour_start=settings.alert_work_hour_start,
            work_hour_end=settings.alert_work_hour_end,
        )
        return ElapsedPair(
            fulfillment=to_fulfillment_stats(
                fulfillment,
                total_created,
                settings.alert_work_hour_start,
                settings.alert_work_hour_end,
            ),
            pending_to_dispatch=to_pending_to_dispatch_stats(
                compute_pending_to_dispatch(data.dispatch_rows, history), total_created
            ),
        )


def _supply_ids_of(data: CustomerAggregates) -> list[int]:
    ids = (supply_id_of(row.internal_order_id) for row in data.dispatch_rows)
    return [supply_id for supply_id in ids if supply_id is not None]


def _build(
    customer_id: int,
    customer_name: str,
    period: StatsRange,
    data: CustomerAggregates,
    elapsed: ElapsedPair,
) -> CustomerStatistics:
    total_created = data.current.get(EVENT_CREATED, 0)
    total_failed = data.current.get(EVENT_FAILED, 0)
    peak_day, peak_day_count = peak_of(data.series, total_created)
    return CustomerStatistics(
        period=period,
        customer_id=customer_id,
        customer_name=customer_name,
        earliest_day=data.earliest_day,
        total_created=total_created,
        total_failed=total_failed,
        success_rate=_pct(total_created, total_created + total_failed),
        previous_created=data.previous.get(EVENT_CREATED, 0),
        previous_failed=data.previous.get(EVENT_FAILED, 0),
        daily_average=round(total_created / period.days, 1),
        peak_day=peak_day,
        peak_day_count=peak_day_count,
        auto_created=data.source_split.auto,
        manual_created=data.source_split.total - data.source_split.auto,
        auto_pct=_pct(data.source_split.auto, data.source_split.total),
        monitored_devices=data.monitored_devices,
        distinct_skus=len(data.top_skus),
        fulfillment=elapsed.fulfillment,
        pending_to_dispatch=elapsed.pending_to_dispatch,
        series=data.series,
        top_skus=data.top_skus[:TOP_SKUS_LIMIT],
        top_devices=data.top_devices,
        failure_reasons=data.failure_reasons,
        recent_failures=data.recent_failures,
    )


def _pct(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0
