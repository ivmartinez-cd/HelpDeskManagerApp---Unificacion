from src.modules.auth.domain.services.mailer import Mailer
from src.modules.auth.infrastructure.console_mailer import ConsoleMailer
from src.modules.auth.infrastructure.smtp_mailer import SmtpConfig, SmtpMailer
from src.shared.infrastructure.config.settings import get_settings


def get_mailer() -> Mailer:
    """SMTP_HOST vacío = consola (ver .env.example) — el mismo criterio que
    ya usan SDSInsumos/STC Cloud para "backup por mail deshabilitado"."""
    settings = get_settings()
    if settings.smtp_host:
        return SmtpMailer(SmtpConfig.general(settings))
    return ConsoleMailer()


def get_mailer_canal_directo() -> Mailer:
    """Avisos que salen "en nombre de Canal Directo" (remitente
    noreply@canaldirecto.com.ar por el relay institucional, `CD_SMTP_*`). Sin
    CD_SMTP_HOST cae al mailer general: el aviso sale igual, con SMTP_FROM."""
    settings = get_settings()
    if settings.cd_smtp_host:
        return SmtpMailer(SmtpConfig.canal_directo(settings))
    return get_mailer()
