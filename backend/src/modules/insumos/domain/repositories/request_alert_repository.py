"""Puerto de las alertas de solicitudes sin cargar (tabla request_alerts).

Alcance portado: la escalada en vivo y el reconocimiento manual — lo que hace el
endpoint. La siembra (`sync_pending_alerts`) y la resolución automática al cargar un
pedido pertenecen al job de fondo de alertas, que todavía no está portado: hasta
entonces la tabla solo tiene lo que haya importado del legacy.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from src.modules.insumos.domain.entities.request_alert import AlertPendingEntry, RequestAlert


class RequestAlertRepository(Protocol):
    async def sync_pending(self, pending: list[AlertPendingEntry]) -> None:
        """Upserta las alertas de solicitudes pendientes y resuelve las que ya no están.

        El upsert nunca pisa state/escalated_at/acknowledged_at de una alerta activa
        (TRIGGERED/ESCALATED/ACKNOWLEDGED) — solo refresca metadata. Si estaba RESOLVED
        y el mismo pedido vuelve a aparecer pendiente, se reabre como TRIGGERED con
        first_seen_at renovado. Las alertas que ya no están en `pending` pasan a RESOLVED.
        """
        ...

    async def escalate_due(self, cutoff: datetime) -> int:
        """Pasa a ESCALATED las TRIGGERED cuyo `requested_at` sea anterior o igual al
        corte y devuelve cuántas. Las que no tienen `requested_at` nunca escalan: sin
        ese dato no se sabe hace cuánto espera el cliente."""
        ...

    async def list_escalated(self) -> list[RequestAlert]:
        """Alertas ESCALATED (las reconocidas ya no son "activas"), la más antigua
        primero — la más urgente arriba."""
        ...

    async def acknowledge(self, hp_request_ids: Sequence[int]) -> int:
        """Marca ACKNOWLEDGED las que estén ESCALATED y devuelve cuántas. Solo desde
        ESCALATED: reconocer algo que todavía no venció no significa nada."""
        ...
