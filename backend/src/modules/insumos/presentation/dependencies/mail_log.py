"""Factory del listado de mails salientes."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.application.use_cases.list_mail_log import (
    ListMailLog,
    ListMailLogPorts,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_mail_log_repository import (
    SqlAlchemyMailLogRepository,
)


def build_list_mail_log(session: AsyncSession) -> ListMailLog:
    return ListMailLog(ListMailLogPorts(mail_log=SqlAlchemyMailLogRepository(session)))
