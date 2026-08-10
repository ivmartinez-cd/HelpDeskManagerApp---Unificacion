"""Puerto del historial permanente (order_audit)."""

from typing import Protocol

from src.modules.insumos.domain.entities.audit_record import AuditRecord


class OrderAuditRepository(Protocol):
    async def record(self, entry: AuditRecord) -> None: ...

    async def count_created_today(self, hp_request_id: int) -> int:
        """Pedidos reales (no dry-run) CREATED hoy (día argentino) para esta solicitud.

        Cuenta sobre order_audit y no sobre processed_requests a propósito: cancelar
        un pedido borra el rastro allá pero nunca acá — es la base del techo anti-abuso
        CANCEL_RELOAD_DAILY_LIMIT (bloqueo 3 de /load, sin bypass)."""
        ...
