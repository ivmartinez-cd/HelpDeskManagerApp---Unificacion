import asyncio
import smtplib
from email.message import EmailMessage

from src.shared.infrastructure.config.settings import Settings


class SmtpMailer:
    """SMTP real vía STARTTLS. `smtplib` es síncrono — se corre en un thread
    aparte para no bloquear el loop de asyncio."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send(
        self, *, to: str, subject: str, body: str, html_body: str | None = None
    ) -> None:
        message = self._build_message(
            to=to, subject=subject, body=body, html_body=html_body
        )
        await asyncio.to_thread(self._send_sync, message)

    def _build_message(
        self, *, to: str, subject: str, body: str, html_body: str | None
    ) -> EmailMessage:
        message = EmailMessage()
        message["From"] = self._settings.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        if html_body is not None:
            message.add_alternative(html_body, subtype="html")
        return message

    def _send_sync(self, message: EmailMessage) -> None:
        with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(self._settings.smtp_user, self._settings.smtp_pass.get_secret_value())
            smtp.send_message(message)
