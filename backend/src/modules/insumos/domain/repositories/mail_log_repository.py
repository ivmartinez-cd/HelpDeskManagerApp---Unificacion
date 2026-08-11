"""Puerto del registro de mails salientes (tabla mail_log).

Solo lectura por ahora: los puntos de envío que escriben acá (backup diario, alerta
de poller caído/recuperado, aviso de pedidos por vencer) viven en los jobs de fondo,
que no están portados. Hasta entonces la tabla se llena únicamente con los datos
importados del legacy.
"""

from typing import Protocol

from src.modules.insumos.domain.value_objects.mail_log_entry import MailLogEntry


class MailLogRepository(Protocol):
    async def list_latest(self, limit: int, offset: int = 0) -> list[MailLogEntry]:
        """Página de mails, más reciente primero (id DESC)."""
        ...

    async def count(self) -> int:
        """Total de filas — el `total` del envelope de paginación. La tabla crece sin
        poda, por eso la paginación es real en SQL y no un recorte en memoria."""
        ...
