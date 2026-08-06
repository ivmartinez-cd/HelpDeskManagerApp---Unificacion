from src.modules.auth.domain.services.mailer import Mailer
from src.modules.auth.infrastructure.console_mailer import ConsoleMailer
from src.modules.auth.infrastructure.smtp_mailer import SmtpMailer
from src.shared.infrastructure.config.settings import get_settings


def get_mailer() -> Mailer:
    """SMTP_HOST vacío = consola (ver .env.example) — el mismo criterio que
    ya usan SDSInsumos/STC Cloud para "backup por mail deshabilitado"."""
    settings = get_settings()
    if settings.smtp_host:
        return SmtpMailer(settings)
    return ConsoleMailer()
