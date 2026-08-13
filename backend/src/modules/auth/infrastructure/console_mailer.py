import logging

logger = logging.getLogger("mail")


class ConsoleMailer:
    """Mailer de dev: el link va al log en vez de a una bandeja real. Nunca
    se usa en producción (ver get_mailer, que elige según SMTP_HOST)."""

    async def send(
        self, *, to: str, subject: str, body: str, html_body: str | None = None
    ) -> None:
        logger.info("Email a %s | %s\n%s", to, subject, body)
