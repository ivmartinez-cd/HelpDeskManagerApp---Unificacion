"""Puerto del registro de mails salientes (tabla mail_log).

Los puntos de envío que escriben acá (alerta de poller caído/recuperado, aviso de
pedidos por vencer) viven en los jobs de fondo — ver `application/jobs/mail_delivery.py`
y `presentation/mail_dispatch.py`.
"""

from typing import Protocol

from src.modules.insumos.domain.value_objects.mail_log_entry import (
    MailLogEntry,
    MailLogRecord,
)


class MailLogRepository(Protocol):
    async def list_latest(self, limit: int, offset: int = 0) -> list[MailLogEntry]:
        """Página de mails, más reciente primero (id DESC)."""
        ...

    async def count(self) -> int:
        """Total de filas — el `total` del envelope de paginación. La tabla crece sin
        poda, por eso la paginación es real en SQL y no un recorte en memoria."""
        ...

    async def record(self, entry: MailLogRecord) -> None:
        """Deja la constancia de un envío lógico. NO commitea: el límite de la
        transacción lo pone el caller (mismo criterio que OrderAuditRepository.record)."""
        ...
