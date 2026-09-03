"""Wiring del Notificador de liquidaciones — separado de `liquidaciones.py`
por tamaño (§4). Sin flag on/off: siempre construye la impl con mail real.
El aviso sale "en nombre de Canal Directo" (noreply@canaldirecto.com.ar por el
relay institucional, `CD_SMTP_*`, como el aviso al cliente de SDSInsumos) y no
desde la cuenta del usuario que opera la app; sin CD_SMTP_HOST cae al SMTP_*
general, que en dev es Mailpit y no sale nada de la máquina."""

from functools import lru_cache

from src.modules.auth.infrastructure.mailer_factory import get_mailer_canal_directo
from src.modules.liquidaciones.domain.repositories.notificador import Notificador
from src.modules.liquidaciones.infrastructure.email_notificador import EmailNotificador
from src.shared.infrastructure.config.settings import get_settings


@lru_cache
def build_notificador() -> Notificador:
    settings = get_settings()
    return EmailNotificador(
        mailer=get_mailer_canal_directo(), frontend_url=settings.frontend_url
    )
