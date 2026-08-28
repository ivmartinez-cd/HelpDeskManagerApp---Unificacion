"""Implementación real de ClientOrderNotifier — arma el mail, lo envía por el SMTP
dedicado al cliente y deja constancia en mail_log. Abre su propia sesión porque
LoadOrder no tiene control sobre cuándo commitea la suya (mismo criterio que
LoggedMailDispatcher, ver presentation/mail_dispatch.py)."""

from src.modules.insumos.application.jobs.mail_delivery import send_mail_to_all
from src.modules.insumos.domain.repositories.mailer import Mailer
from src.modules.insumos.domain.value_objects.client_order_notice import (
    ClientOrderNotice,
    build_client_order_mail,
)
from src.modules.insumos.domain.value_objects.mail_log_entry import (
    KIND_CLIENT_ORDER_NOTICE,
    MailMessage,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_mail_log_repository import (
    SqlAlchemyMailLogRepository,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.database.session import get_sessionmaker


class ClientOrderDispatcher:
    def __init__(self, mailer: Mailer) -> None:
        self._mailer = mailer

    async def notify(self, notice: ClientOrderNotice) -> None:
        subject, body = build_client_order_mail(notice, get_settings().cd_clientes_url)
        message = MailMessage(kind=KIND_CLIENT_ORDER_NOTICE, subject=subject, body=body)
        delivery = await send_mail_to_all(self._mailer, notice.to_emails, message)
        factory = get_sessionmaker()
        async with factory() as session:
            await SqlAlchemyMailLogRepository(session).record(delivery.log)
            await session.commit()
        if delivery.delivered == 0:
            raise RuntimeError(delivery.log.error or "no se pudo enviar el mail al cliente")
