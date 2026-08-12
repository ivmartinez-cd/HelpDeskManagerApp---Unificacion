"""Envío puro a una lista de destinatarios, sin BD — describe el resultado como una
sola fila de mail_log. La escritura a la tabla y la resolución de destinatarios
quedan del lado del caller (ver `presentation/mail_dispatch.py` y
`presentation/background_jobs.py`)."""

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from src.modules.insumos.domain.repositories.mailer import Mailer
from src.modules.insumos.domain.value_objects.mail_log_entry import (
    MailLogRecord,
    MailMessage,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MailDelivery:
    """`log` es la fila de mail_log del envío lógico; `delivered` cuántos
    destinatarios lo recibieron — hay callers que necesitan distinguir
    "ninguno" de "algunos" (ver el arreglo de mark_notified)."""

    log: MailLogRecord
    delivered: int


async def send_mail_to_all(
    mailer: Mailer, recipients: Sequence[str], message: MailMessage
) -> MailDelivery:
    """Envía a cada destinatario (el Mailer manda de a uno) y describe el envío
    como UNA fila: recipients = CSV completo, success solo si no falló ninguno,
    error con el detalle de los que fallaron."""
    errors = await _send_to_each(mailer, recipients, message)
    delivered = len(recipients) - len(errors)
    log = MailLogRecord(
        kind=message.kind,
        recipients=",".join(recipients),
        subject=message.subject,
        success=delivered == len(recipients) and bool(recipients),
        error="; ".join(errors) or None,
    )
    return MailDelivery(log=log, delivered=delivered)


async def _send_to_each(
    mailer: Mailer, recipients: Sequence[str], message: MailMessage
) -> list[str]:
    errors: list[str] = []
    for addr in recipients:
        try:
            await mailer.send(to=addr, subject=message.subject, body=message.body)
        except Exception as exc:
            logger.error("mail_delivery: no se pudo enviar a %s", addr, exc_info=exc)
            errors.append(f"{addr}: {exc}")
    return errors
