"""Puerto del historial permanente (order_audit)."""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.entities.audit_record import (
    AuditRecord,
    AuditSnapshot,
    StoredAuditRecord,
)


class OrderAuditRepository(Protocol):
    async def record(self, entry: AuditRecord) -> None: ...

    async def count_created_today(self, hp_request_id: int) -> int:
        """Pedidos reales (no dry-run) CREATED hoy (día argentino) para esta solicitud.

        Cuenta sobre order_audit y no sobre processed_requests a propósito: cancelar
        un pedido borra el rastro allá pero nunca acá — es la base del techo anti-abuso
        CANCEL_RELOAD_DAILY_LIMIT (bloqueo 3 de /load, sin bypass)."""
        ...

    async def list_latest(self, limit: int, offset: int = 0) -> list[StoredAuditRecord]:
        """Página de eventos, más reciente primero (id DESC) — el Historial."""
        ...

    async def count(self) -> int:
        """Total de eventos — el `total` del envelope de paginación."""
        ...

    async def backfill_snapshots(self, updates: Sequence[AuditSnapshot]) -> None:
        """Completa device_id/initial_* en filas ya existentes (grabadas antes de que
        se capturaran) — ver AuditSnapshot."""
        ...
