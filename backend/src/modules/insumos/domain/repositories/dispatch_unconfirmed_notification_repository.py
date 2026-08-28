"""Puerto de dedup del aviso a logística de "solicitud nueva con pedido despachado sin
confirmar entrega" (dispatch_unconfirmed_notifications) — una fila por hp_request_id ya
avisado, mismo patrón que PendingOrderNotificationRepository."""

from typing import Protocol


class DispatchUnconfirmedNotificationRepository(Protocol):
    async def get_notified_ids(self, hp_request_ids: list[int]) -> set[int]:
        """Batch — devuelve el subconjunto de hp_request_ids ya notificados."""
        ...

    async def mark_notified(self, hp_request_ids: list[int]) -> None:
        """INSERT OR IGNORE: si dos ciclos se solapan, no rompe."""
        ...
