from datetime import datetime
from typing import Protocol


class LoginAttemptRepository(Protocol):
    async def record(self, *, email: str, ip: str | None, succeeded: bool) -> int:
        """Graba y comitea el intento; devuelve su id."""
        ...

    async def mark_succeeded(self, attempt_id: int) -> None: ...
    async def count_recent_failures(self, *, email: str, since: datetime) -> int: ...
