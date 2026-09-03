import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from pydantic import SecretStr

from src.shared.infrastructure.config.settings import Settings


@dataclass(frozen=True)
class SmtpConfig:
    """Un servidor SMTP + remitente. Dos orígenes en `Settings`: el general
    (`SMTP_*`, avisos internos de la app) y el institucional de Canal Directo
    (`CD_SMTP_*`, relay sin auth con remitente noreply@canaldirecto.com.ar)."""

    host: str
    port: int
    user: str
    password: SecretStr
    starttls: bool
    sender: str

    @classmethod
    def general(cls, settings: Settings) -> "SmtpConfig":
        return cls(
            host=settings.smtp_host,
            port=settings.smtp_port,
            user=settings.smtp_user,
            password=settings.smtp_pass,
            starttls=settings.smtp_starttls,
            sender=settings.smtp_from,
        )

    @classmethod
    def canal_directo(cls, settings: Settings) -> "SmtpConfig":
        return cls(
            host=settings.cd_smtp_host,
            port=settings.cd_smtp_port,
            user=settings.cd_smtp_user,
            password=settings.cd_smtp_pass,
            starttls=settings.cd_smtp_starttls,
            sender=settings.cd_smtp_from,
        )


class SmtpMailer:
    """SMTP real vía STARTTLS (si `config.starttls`) con login si hay `user`.
    En dev apunta a Mailpit (sin TLS ni auth) y nada sale de la máquina.
    `smtplib` es síncrono — se corre en un thread aparte para no bloquear el
    loop de asyncio."""

    def __init__(self, config: SmtpConfig) -> None:
        self._config = config

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
        message["From"] = self._config.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        if html_body is not None:
            message.add_alternative(html_body, subtype="html")
        return message

    def _send_sync(self, message: EmailMessage) -> None:
        cfg = self._config
        with smtplib.SMTP(cfg.host, cfg.port, timeout=10) as smtp:
            if cfg.starttls:
                smtp.starttls()
            if cfg.user:
                smtp.login(cfg.user, cfg.password.get_secret_value())
            smtp.send_message(message)
