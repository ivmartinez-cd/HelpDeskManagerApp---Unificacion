"""Caso de uso AutoLoadRequests — port de maybe_auto_load (config.py del legacy),
llamado por el poller de fondo en cada ciclo, después de sync_new_devices.

Reusa ListRequests para el fetch+filtro (OUTSTANDING de clientes habilitados, frescura,
ventana de validación 0%) en vez de reimplementarlo — evita que autocarga y dashboard
diverjan en qué cuenta como elegible (guía §1, DRY). Reusa LoadOrder para la creación:
los bloqueos 0-3 (incluido el tope diario anti-abuso) y la bifurcación a incidente de
kit de mantenimiento se aplican solos, sin repetir esa lógica acá.
"""

import logging
from dataclasses import dataclass
from typing import Protocol

from src.modules.insumos.application.dtos.load_order import LoadOrderCommand, LoadOrderResult
from src.modules.insumos.application.dtos.request_rows import RequestRow
from src.modules.insumos.domain.repositories.insumos_settings_repository import (
    InsumosSettingsRepository,
)
from src.modules.insumos.domain.services.autoload_eligibility import is_autoload_eligible
from src.modules.insumos.domain.value_objects.insumos_settings import (
    InsumosSettings,
    settings_from_raw,
)

logger = logging.getLogger(__name__)


class _ListRequestsPort(Protocol):
    """Lo que AutoLoadRequests necesita de ListRequests — mismo motivo que el resto
    de los puertos del módulo: depender de la interfaz angosta, no de la clase
    concreta (facilita testear con un fake liviano en vez de armar un ListRequests
    real con todas sus dependencias)."""

    async def execute(self, customer_id: int | None) -> list[RequestRow]: ...


class _LoadOrderPort(Protocol):
    async def execute(self, command: LoadOrderCommand) -> LoadOrderResult: ...


@dataclass(frozen=True)
class AutoLoadPorts:
    list_requests: _ListRequestsPort
    load_order: _LoadOrderPort
    settings: InsumosSettingsRepository


@dataclass(frozen=True)
class AutoLoadResult:
    considered: int
    created: int
    skipped: int


class AutoLoadRequests:
    def __init__(self, ports: AutoLoadPorts, max_orders_per_cycle: int) -> None:
        self._ports = ports
        self._max_orders_per_cycle = max_orders_per_cycle

    async def execute(self) -> AutoLoadResult:
        settings = settings_from_raw(await self._ports.settings.get_all())
        if not settings.autoload_enabled:
            return AutoLoadResult(considered=0, created=0, skipped=0)

        rows = await self._ports.list_requests.execute(customer_id=None)
        considered = created = 0
        for row in rows:
            if created >= self._max_orders_per_cycle:
                logger.info(
                    "auto_load: tope de %d pedidos/incidentes alcanzado, corta el ciclo",
                    self._max_orders_per_cycle,
                )
                break
            if not _eligible(row, settings):
                continue
            considered += 1
            if await self._try_load(row):
                created += 1
        return AutoLoadResult(considered=considered, created=created, skipped=considered - created)

    async def _try_load(self, row: RequestRow) -> bool:
        """Un fallo puntual (ambiguo, serie inactiva, error de red) nunca corta el
        ciclo — mismo criterio best-effort que el legacy y que _fetch_for_customer de
        ListRequests. Se loguea con contexto en este punto, no se silencia (guía §6)."""
        command = LoadOrderCommand(
            hp_request_id=row.request_id,
            customer_id=row.customer_id or 0,
            customer_name=row.customer_name or "",
        )
        try:
            result = await self._ports.load_order.execute(command)
        except Exception as exc:
            logger.error(
                "auto_load: fallo inesperado cargando la solicitud %s (cliente %s)",
                row.request_id,
                row.customer_id,
                exc_info=exc,
            )
            return False
        if not result.ok:
            logger.info(
                "auto_load: solicitud %s no se auto-cargó: %s", row.request_id, result.error
            )
        return result.ok


def _eligible(row: RequestRow, settings: InsumosSettings) -> bool:
    if (
        row.order_id is not None
        or row.validation_pending
        or row.percent_left is None
        # Zona con aviso de cambio de sucursal: se aparta del legacy a propósito (que
        # no excluía, solo dejaba constancia en el Historial) — evita que un despacho
        # a la sucursal equivocada salga sin que nadie lo vea a tiempo. Queda para
        # carga manual, igual que en "Cargar seleccionados".
        or row.requiere_cambio_sucursal
    ):
        return False
    return is_autoload_eligible(
        row.days_left, row.percent_left, settings.autoload_max_days, settings.autoload_min_percent
    )
