"""Caso de uso ListMailLog — port de GET /api/mail-log (routers/mail_log.py).

El legacy devolvía una lista pelada con `limit` (tope 2000); acá el contrato es
paginado (ARCHITECTURE_GUIDE §11) y la paginación es real en SQL: mail_log crece con
cada mail enviado y nunca se poda.
"""

from dataclasses import dataclass

from src.modules.insumos.domain.repositories.mail_log_repository import MailLogRepository
from src.modules.insumos.domain.value_objects.mail_log_entry import MailLogEntry


@dataclass(frozen=True)
class ListMailLogPorts:
    mail_log: MailLogRepository


class ListMailLog:
    def __init__(self, ports: ListMailLogPorts) -> None:
        self._ports = ports

    async def execute(self, page: int, size: int) -> tuple[list[MailLogEntry], int]:
        """(filas de la página, total) — más reciente primero."""
        total = await self._ports.mail_log.count()
        entries = await self._ports.mail_log.list_latest(
            limit=size, offset=(page - 1) * size
        )
        return entries, total
