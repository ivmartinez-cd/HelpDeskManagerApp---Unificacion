"""Puerto del estado de colectores DCA (tabla dca_monitors)."""

from collections.abc import Sequence
from typing import Protocol

from src.modules.insumos.domain.value_objects.dca_monitor import DcaMonitorStatus, MonitorKey


class DcaMonitorRepository(Protocol):
    async def upsert(self, entries: Sequence[DcaMonitorStatus]) -> None:
        """Sincroniza el estado de los colectores recibidos de /api/monitors de Insight.
        checked_at = now() en cada upsert — el timestamp de cuándo se verificó."""
        ...

    async def list_offline_monitors(self, stale_hours: int) -> set[MonitorKey]:
        """Colectores confirmados caídos: online=False AND status='ACTIVE' AND checked_at
        dentro de las últimas stale_hours horas (dato fresco).

        Devuelve MonitorKey (customer_id + monitor_name) para evitar la contaminación
        entre colectores homónimos de clientes distintos (bug 3 del legacy)."""
        ...

    async def list_online_customer_ids(self) -> set[int]:
        """Customer IDs donde al menos un colector está online.

        Se usa para marcar monitor_online=True en los MassOutage heurísticos: un
        volumen alto de equipos sin reportar con el colector activo sugiere problema
        de red/sitio, no colector caído."""
        ...
