"""Wiring de los avisos de liquidaciones — separado de `liquidaciones.py`
por tamaño (§4): el Notificador por mail y el repositorio de modificaciones
del prestador que avisa en la campanita.

Notificador: sin flag on/off, siempre construye la impl con mail real.
El aviso sale "en nombre de Canal Directo" (noreply@canaldirecto.com.ar) por
`LIQUIDACIONES_SMTP_*` — relay dedicado (2026-09-03), no `CD_SMTP_*`: ese lo
comparte el reset/activación de clave de auth, y este dev lo prueban varios
compañeros, así que aislarlo evita que habilitar mail real acá arrastre auth.
Sin LIQUIDACIONES_SMTP_HOST cae a CD_SMTP_*/SMTP_* (Mailpit en dev, nada sale
de la máquina)."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.mailer_factory import get_mailer_liquidaciones
from src.modules.liquidaciones.domain.repositories.modificacion_prestador_repository import (
    ModificacionPrestadorRepository,
)
from src.modules.liquidaciones.domain.repositories.notificador import Notificador
from src.modules.liquidaciones.infrastructure.email_notificador import EmailNotificador
from src.modules.liquidaciones.infrastructure.repositories.modificaciones_con_aviso import (
    ModificacionesConAviso,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_modificacion_prestador_repository import (  # noqa: E501
    SqlAlchemyModificacionPrestadorRepository,
)
from src.modules.notificaciones.infrastructure.repositories.sqlalchemy_notificacion_repository import (  # noqa: E501
    SqlAlchemyNotificacionRepository,
)
from src.shared.infrastructure.config.settings import get_settings


@lru_cache
def build_notificador() -> Notificador:
    settings = get_settings()
    return EmailNotificador(
        mailer=get_mailer_liquidaciones(), cd_base_url=settings.cd_base_url
    )


def build_modificaciones_con_aviso(session: AsyncSession) -> ModificacionPrestadorRepository:
    """Repositorio de modificaciones del prestador que además avisa en la
    campanita (ADR-041), en la misma sesión que la reconciliación."""
    return ModificacionesConAviso(
        SqlAlchemyModificacionPrestadorRepository(session),
        SqlAlchemyLiquidacionRepository(session),
        SqlAlchemyNotificacionRepository(session),
    )
