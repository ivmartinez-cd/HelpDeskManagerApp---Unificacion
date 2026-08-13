from typing import Protocol


class Mailer(Protocol):
    """`body` es texto plano; `html_body` opcional agrega la alternativa
    text/html (multipart) para los mails con layout (vacaciones)."""

    async def send(
        self, *, to: str, subject: str, body: str, html_body: str | None = None
    ) -> None: ...
