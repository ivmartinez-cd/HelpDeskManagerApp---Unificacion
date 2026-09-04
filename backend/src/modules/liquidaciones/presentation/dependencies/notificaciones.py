"""Wiring del Notificador de liquidaciones — separado de `liquidaciones.py`
por tamaño (§4). Sin flag on/off: siempre construye la impl con mail real.
El aviso sale "en nombre de Canal Directo" (noreply@canaldirecto.com.ar) por
`LIQUIDACIONES_SMTP_*` — relay dedicado (2026-09-03), no `CD_SMTP_*`: ese lo
comparte el reset/activación de clave de auth, y este dev lo prueban varios
compañeros, así que aislarlo evita que habilitar mail real acá arrastre auth.
Sin LIQUIDACIONES_SMTP_HOST cae a CD_SMTP_*/SMTP_* (Mailpit en dev, nada sale
de la máquina)."""

from functools import lru_cache

from src.modules.auth.infrastructure.mailer_factory import get_mailer_liquidaciones
from src.modules.liquidaciones.domain.repositories.notificador import Notificador
from src.modules.liquidaciones.infrastructure.email_notificador import EmailNotificador
from src.shared.infrastructure.config.settings import get_settings


@lru_cache
def build_notificador() -> Notificador:
    settings = get_settings()
    return EmailNotificador(
        mailer=get_mailer_liquidaciones(), cd_base_url=settings.cd_base_url
    )
