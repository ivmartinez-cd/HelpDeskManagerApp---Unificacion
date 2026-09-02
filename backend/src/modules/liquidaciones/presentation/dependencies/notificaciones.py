"""Wiring del Notificador de liquidaciones — separado de `liquidaciones.py`
por tamaño (§4). Sin flag on/off: siempre construye la impl con mail real;
`get_mailer()` ya elige SMTP real o consola según SMTP_HOST (mismo mecanismo
que auth/vacaciones — en dev, SMTP_HOST=mailpit y no sale nada de la máquina)."""

from functools import lru_cache

from src.modules.auth.infrastructure.mailer_factory import get_mailer
from src.modules.liquidaciones.domain.repositories.notificador import Notificador
from src.modules.liquidaciones.infrastructure.email_notificador import EmailNotificador
from src.shared.infrastructure.config.settings import get_settings


@lru_cache
def build_notificador() -> Notificador:
    settings = get_settings()
    return EmailNotificador(mailer=get_mailer(), frontend_url=settings.frontend_url)
