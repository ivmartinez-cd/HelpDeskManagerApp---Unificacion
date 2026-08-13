"""Impl con emails del seam `Notificador` (Entrega 3, D8).

Paridad con `vacation.controller.ts` legacy: la nueva solicitud se avisa a los
jefes del sector del empleado + todos los admins (deduplicados), la decisión al
email del empleado. Igual que el `sendMail` legacy, un fallo de envío NUNCA
corta el flujo de la solicitud: se loguea acá y se sigue."""

import logging
import uuid
from typing import Protocol

from src.modules.auth.domain.services.mailer import Mailer
from src.modules.vacaciones.domain.repositories.notificador import (
    DecisionNotif,
    NuevaSolicitudNotif,
)
from src.modules.vacaciones.infrastructure.email_templates import (
    EmailContent,
    email_decision,
    email_nueva_solicitud,
)

_logger = logging.getLogger(__name__)


class DestinatariosNuevaSolicitud(Protocol):
    """Emails que deben enterarse de una solicitud nueva: jefes del sector
    indicado + admins del módulo (impl: sqlalchemy_destinatarios)."""

    async def emails(self, department_id: uuid.UUID) -> list[str]: ...


class EmailNotificador:
    def __init__(
        self,
        mailer: Mailer,
        destinatarios: DestinatariosNuevaSolicitud,
        frontend_url: str,
    ) -> None:
        self._mailer = mailer
        self._destinatarios = destinatarios
        self._frontend_url = frontend_url

    async def notificar_nueva_solicitud(self, notif: NuevaSolicitudNotif) -> None:
        try:
            emails = await self._destinatarios.emails(notif.department_id)
            if not emails:
                _logger.warning(
                    "email_notificador: sin destinatarios para la nueva solicitud",
                    extra={"empleado": notif.empleado_nombre, "sector": notif.sector_nombre},
                )
                return
            contenido = email_nueva_solicitud(notif, self._frontend_url)
            for email in emails:
                await self._enviar(contenido, to=email, contexto=notif.empleado_nombre)
        except Exception as exc:  # el envío jamás corta la creación (paridad legacy)
            _logger.error(
                "email_notificador: falló el aviso de nueva solicitud",
                extra={"empleado": notif.empleado_nombre},
                exc_info=exc,
            )

    async def notificar_decision(self, notif: DecisionNotif) -> None:
        try:
            contenido = email_decision(notif)
            await self._enviar(
                contenido, to=notif.empleado_email, contexto=notif.empleado_nombre
            )
        except Exception as exc:  # ídem: la decisión ya está tomada y persistida
            _logger.error(
                "email_notificador: falló el aviso de decisión",
                extra={"empleado": notif.empleado_nombre, "to": notif.empleado_email},
                exc_info=exc,
            )

    async def _enviar(self, contenido: EmailContent, *, to: str, contexto: str) -> None:
        """Un destinatario fallido no impide el resto (paridad del loop legacy)."""
        try:
            await self._mailer.send(
                to=to,
                subject=contenido.subject,
                body=contenido.text,
                html_body=contenido.html,
            )
        except Exception as exc:
            _logger.error(
                "email_notificador: error enviando email",
                extra={"to": to, "subject": contenido.subject, "empleado": contexto},
                exc_info=exc,
            )
