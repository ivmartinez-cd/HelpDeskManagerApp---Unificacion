"""Puerto de despacho de mails de jobs de fondo — resuelve destinatarios, envía y
deja constancia en mail_log (ver `application/jobs/mail_delivery.py` y
`presentation/mail_dispatch.py` para la implementación real)."""

from typing import Protocol

from src.modules.insumos.domain.value_objects.mail_log_entry import MailMessage


class MailDispatcher(Protocol):
    async def dispatch(self, message: MailMessage) -> None:
        """Resuelve destinatarios, envía y deja constancia en mail_log.

        CONTRATO: nunca propaga. Ni un fallo de SMTP ni uno de la BD deben
        tumbar al job que lo llama."""
        ...
