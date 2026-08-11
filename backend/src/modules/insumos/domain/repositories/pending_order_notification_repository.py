"""Puerto de dedup de avisos de pedidos por vencer (pending_order_notifications).

Una fila por hp_request_id ya avisado — garantiza que el mail de "dar curso en
Canal Directo" se envía una sola vez por pedido, no en cada ciclo del job.
"""

from typing import Protocol


class PendingOrderNotificationRepository(Protocol):
    async def get_notified_ids(self, hp_request_ids: list[int]) -> set[int]:
        """Batch — devuelve el subconjunto de hp_request_ids ya notificados."""
        ...

    async def mark_notified(self, hp_request_ids: list[int]) -> None:
        """INSERT OR IGNORE: si dos ciclos se solapan por algún motivo, no rompe."""
        ...
