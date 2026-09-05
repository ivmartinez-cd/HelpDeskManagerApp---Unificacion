"""Despacho del mail de activación/reset fuera del request.

El token ya quedó comiteado por `get_db(scope="function")` cuando la
respuesta sale; el envío SMTP corre después, en `BackgroundTasks`, así la
latencia del 202 no depende de si hubo mail o no (anti-enumeración)."""

import logging

from fastapi import BackgroundTasks

from src.modules.auth.application.use_cases.request_password_reset import PendingMail
from src.modules.auth.domain.services.mailer import Mailer
from src.modules.auth.infrastructure.mailer_factory import get_mailer_canal_directo

logger = logging.getLogger(__name__)


def encolar_mail(background_tasks: BackgroundTasks, mail: PendingMail | None) -> None:
    if mail is None:
        return
    # Remitente institucional (noreply@canaldirecto.com.ar), no el SMTP_FROM
    # personal del mailer general.
    background_tasks.add_task(_enviar, get_mailer_canal_directo(), mail)


async def _enviar(mailer: Mailer, mail: PendingMail) -> None:
    try:
        await mailer.send(to=mail.to, subject=mail.subject, body=mail.body)
    except Exception:
        # Ya se respondió 202: no hay a quién propagarle el error, pero un
        # reset que no llega tiene que quedar en el log.
        logger.exception(
            "No se pudo enviar el mail de clave", extra={"to": mail.to, "subject": mail.subject}
        )
