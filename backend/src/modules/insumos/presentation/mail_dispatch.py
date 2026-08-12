"""Implementación real de MailDispatcher para los jobs de fondo."""

import logging

from src.modules.insumos.application.jobs.mail_delivery import send_mail_to_all
from src.modules.insumos.domain.repositories.mailer import Mailer
from src.modules.insumos.domain.value_objects.insumos_settings import (
    ops_alert_recipients,
    settings_from_raw,
)
from src.modules.insumos.domain.value_objects.mail_log_entry import MailMessage
from src.modules.insumos.infrastructure.repositories.sqlalchemy_insumos_settings_repository import (  # noqa: E501
    SqlAlchemyInsumosSettingsRepository,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_mail_log_repository import (
    SqlAlchemyMailLogRepository,
)
from src.shared.infrastructure.database.session import get_sessionmaker

logger = logging.getLogger(__name__)


class LoggedMailDispatcher:
    """MailDispatcher de los jobs de fondo: resuelve los destinatarios
    TÉCNICOS (ops_alert_mail_to) frescos, envía y registra en mail_log. Abre
    su propia sesión porque los jobs no tienen una del request — por eso vive
    en presentation y no en infrastructure. Toda la lógica testeable está en
    send_mail_to_all.

    Hoy el único caller es PollerAlerts (kind=poller_alert/poller_recovery) —
    por diseño, este dispatcher NUNCA debe resolver logistics_recipients: esas
    son alertas de negocio para logística (pedidos por vencer), estas son
    alertas técnicas de que el sistema dejó de funcionar. Mezclar las dos
    bandejas fue exactamente el incidente real del 2026-08-12 (ver CLAUDE.md).
    Si en el futuro se agrega un tercer `kind` a este dispatcher que SÍ deba
    ir a logística, hay que branchear por `message.kind` acá — no asumir."""

    def __init__(self, mailer: Mailer) -> None:
        self._mailer = mailer

    async def dispatch(self, message: MailMessage) -> None:
        try:
            await self._dispatch(message)
        except Exception as exc:
            logger.error(
                "mail_dispatch: falló el envío/registro de %s", message.kind, exc_info=exc
            )

    async def _dispatch(self, message: MailMessage) -> None:
        factory = get_sessionmaker()
        async with factory() as session:
            raw = await SqlAlchemyInsumosSettingsRepository(session).get_all()
            recipients = ops_alert_recipients(settings_from_raw(raw))
            if not recipients:
                logger.warning("mail_dispatch: sin destinatarios, se omite %s", message.kind)
                return
            delivery = await send_mail_to_all(self._mailer, recipients, message)
            await SqlAlchemyMailLogRepository(session).record(delivery.log)
            await session.commit()
