from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NuevaSolicitudNotif:
    empleado_nombre: str
    sector_nombre: str
    start_date: date
    end_date: date
    dias: int
    target_year: int
    reason: str | None


@dataclass(frozen=True, slots=True)
class DecisionNotif:
    empleado_nombre: str
    empleado_email: str
    aprobada: bool
    start_date: date
    end_date: date
    comment: str | None


class Notificador(Protocol):
    """Seam de notificaciones (D8 del plan). En la Entrega 1 la única impl es
    LoggingNotificador; los emails del legacy (nueva solicitud → admins y
    jefes del sector; decisión → empleado) se enchufan acá en una entrega
    posterior sin tocar contratos."""

    async def notificar_nueva_solicitud(self, notif: NuevaSolicitudNotif) -> None: ...

    async def notificar_decision(self, notif: DecisionNotif) -> None: ...
