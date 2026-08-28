"""SMTP dedicado del aviso al cliente (CLIENT_MAIL_SMTP_*) — separado del `Mailer`
interno (SMTP_*, backup/alertas a destinatarios internos): este manda a clientes
externos y necesita su propio remitente/relay. Mismo shape que el `Mailer` interno
(auth/infrastructure/smtp_mailer.py) para poder reusar
application/jobs/mail_delivery.py::send_mail_to_all sin duplicar esa lógica."""

import asyncio
import smtplib
from email.message import EmailMessage

from src.shared.infrastructure.config.settings import Settings

_SMTP_TIMEOUT_SECONDS = 15


class ClientOrderMailer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send(self, *, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._settings.client_mail_sender_email
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> None:
        settings = self._settings
        with smtplib.SMTP(
            settings.client_mail_smtp_host,
            settings.client_mail_smtp_port,
            timeout=_SMTP_TIMEOUT_SECONDS,
        ) as smtp:
            if settings.client_mail_smtp_use_tls:
                smtp.starttls()
            if settings.client_mail_smtp_username:
                smtp.login(
                    settings.client_mail_smtp_username,
                    settings.client_mail_smtp_password.get_secret_value(),
                )
            smtp.send_message(message)
