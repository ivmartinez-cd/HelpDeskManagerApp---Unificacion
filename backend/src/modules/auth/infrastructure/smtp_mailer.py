import asyncio
import smtplib
from email.message import EmailMessage

from src.shared.infrastructure.config.settings import Settings


class SmtpMailer:
    """SMTP real vía STARTTLS (SMTP_STARTTLS=true, default) con login si hay
    SMTP_USER. En dev apunta a Mailpit (sin TLS ni auth) y nada sale de la
    máquina. `smtplib` es síncrono — se corre en un thread aparte para no
    bloquear el loop de asyncio."""

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
        settings = self._settings
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_starttls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_pass.get_secret_value())
            smtp.send_message(message)
