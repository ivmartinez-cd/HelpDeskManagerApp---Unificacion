import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.modules.auth.domain.entities.password_reset_token import PasswordResetToken
from src.modules.auth.domain.repositories.reset_token_repository import ResetTokenRepository
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.services.mailer import Mailer
from src.modules.auth.domain.services.session_token_generator import SessionTokenGenerator
from src.modules.auth.domain.value_objects.email import Email

_TOKEN_TTL = timedelta(minutes=30)


@dataclass(frozen=True, slots=True)
class RequestPasswordResetDependencies:
    users: UserRepository
    reset_tokens: ResetTokenRepository
    tokens: SessionTokenGenerator
    mailer: Mailer
    frontend_url: str


class RequestPasswordReset:
    """Anti-enumeración: si el email no existe, no se manda nada — pero
    tampoco se informa la diferencia. El caller (router) responde 202 igual
    en ambos casos, con el mismo body y sin ninguna rama que tome menos
    tiempo (no hay early return con latencia distinta)."""

    def __init__(self, deps: RequestPasswordResetDependencies) -> None:
        self._deps = deps

    async def execute(self, email: str) -> None:
        user = await self._deps.users.get_by_email(Email(email))
        if user is None:
            return
        token = self._deps.tokens.generate()
        await self._deps.reset_tokens.add(
            PasswordResetToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token_hash=self._deps.tokens.hash(token),
                expires_at=datetime.now(UTC) + _TOKEN_TTL,
            )
        )
        link = f"{self._deps.frontend_url}/reset-password?token={token}"
        await self._deps.mailer.send(
            to=user.email.value,
            subject="Restablecer tu contraseña — HelpDesk Manager",
            body=f"Usá este link para restablecer tu contraseña (vence en 30 minutos): {link}",
        )
