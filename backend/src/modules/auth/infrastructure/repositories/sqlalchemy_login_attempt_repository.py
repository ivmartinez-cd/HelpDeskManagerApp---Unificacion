from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.session_model import LoginAttempt


class SqlAlchemyLoginAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, *, email: str, ip: str | None, succeeded: bool) -> None:
        """Único repositorio que comitea a propósito (excepción documentada a
        `flush`-only): es un registro de auditoría/rate-limit, tiene que
        sobrevivir aunque el flujo que lo originó levante una excepción
        justo después (ej. AuthenticateUser registrando un intento fallido y
        acto seguido lanzando InvalidCredentialsError)."""
        self._session.add(LoginAttempt(email=email, ip=ip, succeeded=succeeded))
        await self._session.commit()

    async def count_recent_failures(self, *, email: str, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.email == email,
                LoginAttempt.succeeded.is_(False),
                LoginAttempt.attempted_at >= since,
            )
        )
        return (await self._session.execute(stmt)).scalar_one()
