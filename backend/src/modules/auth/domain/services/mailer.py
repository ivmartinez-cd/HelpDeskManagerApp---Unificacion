from typing import Protocol


class Mailer(Protocol):
    async def send(self, *, to: str, subject: str, body: str) -> None: ...
