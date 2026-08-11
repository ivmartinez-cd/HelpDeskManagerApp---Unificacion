"""Agregación pura del dashboard — port de la fase 4 de compute_dashboard_state.

Sin I/O: recibe las solicitudes ya resueltas (snapshots), el cache de supplies por serie
y las órdenes propias, y produce los conteos por cliente + totales, con el mismo criterio
de "cargada" y de severidad que el legacy.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from src.modules.insumos.domain.entities.processed_request import ProcessedRequest
from src.modules.insumos.domain.services.supply_request_matching import (
    SupplyMatchQuery,
    match_active_supply,
    match_supply_for_request,
    supply_matches_request,
)
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings


@dataclass(frozen=True)
class RequestSnapshot:
    """Una solicitud OUTSTANDING ya resuelta contra Insight (no-stale)."""

    hp_request_id: int
    device_id: int
    device_serial: str  # "" si Insight no devolvió serie
    sku: str
    description: str
    days_left: int | None
    requested_day: date | None  # día argentino de `requested`
    is_maintenance_kit: bool = False


@dataclass(frozen=True)
class CustomerRequests:
    customer_id: int
    name: str
    requests: tuple[RequestSnapshot, ...]
    processed_ids: frozenset[int]
    error: str | None = None


@dataclass(frozen=True)
class CustomerSummary:
    customer_id: int
    name: str
    pending: int = 0
    critical: int = 0
    urgent: int = 0
    warning: int = 0
    good: int = 0
    loaded: int = 0
    error: str | None = None


SuppliesBySerial = Mapping[str, Sequence[CachedSupply]]
OwnOrdersBySerial = Mapping[str, Sequence[ProcessedRequest]]


def summarize_customers(
    datas: Sequence[CustomerRequests],
    settings: InsumosSettings,
    supplies_by_serial: SuppliesBySerial,
    own_orders_by_serial: OwnOrdersBySerial,
) -> tuple[list[CustomerSummary], dict[str, int]]:
    """(por-cliente ordenado por gravedad, totales). Mismo orden que el legacy:
    más críticos primero, después urgentes/advertencia/buenos/pendientes, y nombre."""
    per_customer = [
        _summarize_one(data, settings, supplies_by_serial, own_orders_by_serial)
        for data in datas
    ]
    totals = {"pending": 0, "critical": 0, "urgent": 0, "warning": 0, "good": 0, "loaded": 0}
    for entry in per_customer:
        for key in totals:
            totals[key] += getattr(entry, key)
    per_customer.sort(
        key=lambda e: (-e.critical, -e.urgent, -e.warning, -e.good, -e.pending, e.name)
    )
    return per_customer, totals


def _summarize_one(
    data: CustomerRequests,
    settings: InsumosSettings,
    supplies_by_serial: SuppliesBySerial,
    own_orders_by_serial: OwnOrdersBySerial,
) -> CustomerSummary:
    counts = {"pending": 0, "critical": 0, "urgent": 0, "warning": 0, "good": 0, "loaded": 0}
    for request in data.requests:
        if _is_loaded(request, data.processed_ids, supplies_by_serial, own_orders_by_serial):
            counts["loaded"] += 1
            continue
        counts["pending"] += 1
        counts[_severity(request.days_left, settings)] += 1
    return CustomerSummary(
        customer_id=data.customer_id, name=data.name, error=data.error, **counts
    )


def _is_loaded(
    request: RequestSnapshot,
    processed_ids: frozenset[int],
    supplies_by_serial: SuppliesBySerial,
    own_orders_by_serial: OwnOrdersBySerial,
) -> bool:
    """Cargada = registrada por esta app, o cubierta por un supply del cache que
    matchea el consumible (criterio UI: nunca ocultar una solicitud detrás de un
    pedido no confirmado — for_ui_display=True)."""
    if request.hp_request_id in processed_ids:
        return True
    if not request.device_serial:
        return False
    serial_key = request.device_serial.upper()
    supplies = supplies_by_serial.get(serial_key, ())
    query = SupplyMatchQuery(
        sku=request.sku,
        description=request.description,
        own_orders=tuple(own_orders_by_serial.get(serial_key, ())),
    )
    active = match_active_supply(supplies)
    if active is not None and supply_matches_request(active, query, for_ui_display=True):
        return True
    recent = match_supply_for_request(supplies, request.requested_day)
    return recent is not None and supply_matches_request(recent, query, for_ui_display=True)


def _severity(days_left: int | None, settings: InsumosSettings) -> str:
    # daysLeft siempre viene en las solicitudes reales de Insight; un None (nunca
    # observado) se trata como "good" en vez de romper el dashboard entero.
    if days_left is None:
        return "good"
    if days_left <= settings.threshold_critical:
        return "critical"
    if days_left <= settings.threshold_urgent:
        return "urgent"
    if days_left <= settings.threshold_warning:
        return "warning"
    return "good"
