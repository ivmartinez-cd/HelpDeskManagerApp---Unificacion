"""Puerto del historial permanente (order_audit)."""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.entities.audit_record import (
    AuditRecord,
    AuditSnapshot,
    StoredAuditRecord,
)
from src.modules.insumos.domain.value_objects.audit_history import AuditClosures, AuditFilters


class OrderAuditRepository(Protocol):
    async def record(self, entry: AuditRecord) -> None: ...

    async def count_created_today(self, hp_request_id: int) -> int:
        """Pedidos reales (no dry-run) CREATED hoy (día argentino) para esta solicitud.

        Cuenta sobre order_audit y no sobre processed_requests a propósito: cancelar
        un pedido borra el rastro allá pero nunca acá — es la base del techo anti-abuso
        CANCEL_RELOAD_DAILY_LIMIT (bloqueo 3 de /load, sin bypass)."""
        ...

    async def list_page(
        self, filters: AuditFilters, limit: int, offset: int
    ) -> list[StoredAuditRecord]:
        """Página de eventos que matchean `filters`, más reciente primero (id DESC)
        — el Historial."""
        ...

    async def count(self, filters: AuditFilters) -> int:
        """Total de eventos que matchean `filters` — el `total` del envelope de
        paginación."""
        ...

    async def count_by_event(self, filters: AuditFilters) -> dict[str, int]:
        """Conteo por evento que matchea `filters` — los badges de las pestañas
        del Historial."""
        ...

    async def closures_for(self, hp_request_ids: Sequence[int]) -> AuditClosures:
        """Ignora los filtros a propósito: la acción de una fila depende de TODA la
        tabla, no de lo que el operador esté filtrando en este momento."""
        ...

    async def backfill_snapshots(self, updates: Sequence[AuditSnapshot]) -> None:
        """Completa device_id/initial_* en filas ya existentes (grabadas antes de que
        se capturaran) — ver AuditSnapshot."""
        ...
