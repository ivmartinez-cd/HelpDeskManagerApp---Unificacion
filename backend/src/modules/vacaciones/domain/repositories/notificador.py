import uuid
from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NuevaSolicitudNotif:
    empleado_nombre: str
    sector_nombre: str
    # El sector del empleado: la impl con emails lo usa para resolver a los
    # jefes de ese sector como destinatarios (paridad legacy).
    department_id: uuid.UUID
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
    """Seam de notificaciones (D8 del plan). Impls: LoggingNotificador (log,
    default) y EmailNotificador (Entrega 3 — nueva solicitud → admins y jefes
    del sector; decisión → empleado), elegidas en presentation según
    `vacaciones_mail_enabled`."""

    async def notificar_nueva_solicitud(self, notif: NuevaSolicitudNotif) -> None: ...

    async def notificar_decision(self, notif: DecisionNotif) -> None: ...
