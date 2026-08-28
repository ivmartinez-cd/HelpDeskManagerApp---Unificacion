"""Puerto de processed_requests — el núcleo de la idempotencia.

"Hoy" siempre es el día calendario en America/Argentina/Buenos_Aires (criterio de
negocio del legacy: `date(created_at, 'localtime')`), nunca el día UTC ni la zona del
servidor. La implementación vive en infrastructure/repositories/.
"""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.entities.processed_request import (
    ProcessedInitialSnapshot,
    ProcessedRequest,
)


class ProcessedRequestRepository(Protocol):
    async def get(self, hp_request_id: int) -> ProcessedRequest | None: ...

    async def mark_processed(self, request: ProcessedRequest) -> None:
        """Upsert por hp_request_id (reprocesar una solicitud pisa el registro previo)."""
        ...

    async def mark_cancelled(self, hp_request_id: int) -> None:
        """Nunca borra la fila: pasa a STATUS_CANCELLED — la solicitud puede recargarse
        a mano pero la autocarga no debe repetirla."""
        ...

    async def get_today_order_for(self, device_serial: str, sku: str) -> ProcessedRequest | None:
        """Pedido CREATED cargado HOY (día argentino) para esta serie+sku exactas —
        insumo del bloqueo 1 de /load."""
        ...

    async def get_created_by_serial(self, device_serial: str) -> list[ProcessedRequest]:
        """Órdenes CREATED de la serie (case-insensitive), más recientes primero —
        el `own_orders` del matching anti-duplicados."""
        ...

    async def get_processed_ids(self, hp_request_ids: Sequence[int]) -> set[int]:
        """Subset de los ids que ya tienen pedido CREATED."""
        ...

    async def get_supply_ids(self, hp_request_ids: Sequence[int]) -> dict[int, int]:
        """{hp_request_id: supply_id numérico} de pedidos reales CREATED (excluye
        DRYRUN y los no parseables)."""
        ...

    async def get_today_processed_ids(self, hp_request_ids: Sequence[int]) -> set[int]:
        """Subset cuyo pedido fue creado HOY (día argentino)."""
        ...

    async def count_processed_today(self) -> int:
        """Pedidos CREATED de hoy (día argentino) — el tile "cargados hoy"."""
        ...

    async def get_created_by_serials(
        self, device_serials: Sequence[str]
    ) -> dict[str, list[ProcessedRequest]]:
        """Versión batch de get_created_by_serial (keyed serial.upper()) — anti N+1."""
        ...

    async def get_all_created(self, customer_id: int | None = None) -> list[ProcessedRequest]:
        """Todas las órdenes CREATED (opcionalmente de un cliente), más recientes
        primero — la base del seguimiento de pedidos pendientes."""
        ...

    async def backfill_initial_snapshot(
        self, updates: Sequence[ProcessedInitialSnapshot]
    ) -> None:
        """Completa initial_* en filas ya existentes (ver ProcessedInitialSnapshot)."""
        ...

    async def get_missing_consumable_serial(
        self, within_days: int | None = None
    ) -> list[ProcessedRequest]:
        """Pedidos CREATED sin consumable_serial — candidatos para completar vía Insight
        (ver application/use_cases/backfill_consumable_serial.py). `within_days=None` trae
        todo el historial (script manual); un número acota a los últimos N días (chequeo
        periódico del poller)."""
        ...

    async def backfill_consumable_serial(self, updates: Sequence[tuple[int, str]]) -> None:
        """Completa consumable_serial en filas ya existentes. Cada entry:
        (hp_request_id, consumable_serial)."""
        ...

    async def find_consumable_serial_reuse_batch(
        self, consumable_serials: set[str]
    ) -> dict[str, list[ProcessedRequest]]:
        """Pedidos previos (cualquier serie) que ya usaron cada consumable_serial — señal
        de cartucho reinstalado o movido de equipo, puramente informativa (nunca decide un
        match). Keyed por consumable_serial.upper(), listas ordenadas por created_at DESC."""
        ...
