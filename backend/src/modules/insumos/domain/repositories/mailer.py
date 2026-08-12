"""Puerto de envío de mails. Duplicado del Protocol de auth (no importado de ahí):
ADR-007 prohíbe que insumos.domain/application dependa de auth."""

from typing import Protocol


class Mailer(Protocol):
    async def send(self, *, to: str, subject: str, body: str) -> None: ...
