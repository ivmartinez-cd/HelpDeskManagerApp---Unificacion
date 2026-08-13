import logging

from src.modules.vacaciones.domain.repositories.notificador import (
    DecisionNotif,
    NuevaSolicitudNotif,
)

_logger = logging.getLogger(__name__)


class LoggingNotificador:
    """Única impl del seam de notificaciones en la Entrega 1 (D8): loguea en
    vez de mandar. Los emails del legacy se enchufan acá cuando se decida
    activarlos (nueva solicitud → admins y jefes del sector; decisión →
    empleado)."""

    async def notificar_nueva_solicitud(self, notif: NuevaSolicitudNotif) -> None:
        _logger.info(
            "Nueva solicitud de vacaciones: %s (%s) %s → %s (%d días, ciclo %d)",
            notif.empleado_nombre,
            notif.sector_nombre,
            notif.start_date,
            notif.end_date,
            notif.dias,
            notif.target_year,
        )

    async def notificar_decision(self, notif: DecisionNotif) -> None:
        _logger.info(
            "Solicitud %s para %s <%s>: %s → %s",
            "APROBADA" if notif.aprobada else "RECHAZADA",
            notif.empleado_nombre,
            notif.empleado_email,
            notif.start_date,
            notif.end_date,
        )
