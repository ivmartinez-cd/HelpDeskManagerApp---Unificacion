"""Puerto de processed_requests — el núcleo de la idempotencia.

"Hoy" siempre es el día calendario en America/Argentina/Buenos_Aires (criterio de
negocio del legacy: `date(created_at, 'localtime')`), nunca el día UTC ni la zona del
servidor. La implementación vive en infrastructure/repositories/.
"""

from typing import Protocol

from src.modules.insumos.domain.entities.processed_request import ProcessedRequest


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
