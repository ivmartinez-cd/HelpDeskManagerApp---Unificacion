"""Value objects para el estado de colectores DCA (dca_monitors)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MonitorKey:
    """Par (customer_id, monitor_name) — hashable, usable como clave de set/dict.

    El legacy solo usaba monitor_name como str: colectores homónimos de clientes distintos
    se excluían mutuamente de la baja (bug 3 del relevamiento). Al incluir customer_id en
    el tipo, el contrato de list_offline_monitors fuerza la clave completa sin comentarios.
    """

    customer_id: int
    monitor_name: str


@dataclass(frozen=True)
class DcaMonitorStatus:
    """Estado de un colector tal como viene de /api/monitors de Insight — valor de upsert."""

    customer_id: int
    monitor_name: str
    online: bool
    status: str
    last_contact: datetime | None
    checked_at: datetime
