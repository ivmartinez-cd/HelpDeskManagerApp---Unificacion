import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from src.modules.auth.domain.entities.password_reset_token import PasswordResetToken
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.repositories.reset_token_repository import ResetTokenRepository
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.services.session_token_generator import SessionTokenGenerator
from src.modules.auth.domain.value_objects.email import Email

_TOKEN_TTL = timedelta(minutes=30)
# Límite de frecuencia: más de esto en la ventana y no se emite otro token
# (ni mail) — la respuesta al cliente es la misma.
_MAX_TOKENS_PER_WINDOW = 3
_RATE_WINDOW = timedelta(minutes=15)

ResetPurpose = Literal["activation", "reset"]

_SUBJECTS: dict[ResetPurpose, str] = {
    "activation": "Activá tu cuenta — HelpDesk Manager",
    "reset": "Restablecer tu contraseña — HelpDesk Manager",
}
_BODIES: dict[ResetPurpose, str] = {
    "activation": "Usá este link para activar tu cuenta y elegir tu contraseña "
    "(vence en 30 minutos): {link}",
    "reset": "Usá este link para restablecer tu contraseña (vence en 30 minutos): {link}",
}


@dataclass(frozen=True, slots=True)
class PendingMail:
    """Mail a despachar por el caller (fuera del request, ver auth_router):
    el caso de uso no envía nada, solo persiste el token y arma el mensaje."""

    to: str
    subject: str
    body: str


@dataclass(frozen=True, slots=True)
class RequestPasswordResetDependencies:
    users: UserRepository
    reset_tokens: ResetTokenRepository
    tokens: SessionTokenGenerator
    frontend_url: str


class RequestPasswordReset:
    """Anti-enumeración: si el email no existe, la cuenta está inactiva o se
    superó el límite de frecuencia, devuelve None — pero no informa la
    diferencia. El caller (router) responde 202 igual en todos los casos, con
    el mismo body, y manda el mail en segundo plano para que la latencia del
    request no delate qué rama se tomó."""

    def __init__(self, deps: RequestPasswordResetDependencies) -> None:
        self._deps = deps

    async def execute(self, email: str, *, purpose: ResetPurpose = "reset") -> PendingMail | None:
        user = await self._deps.users.get_by_email(Email(email))
        if user is None or not user.is_active or await self._over_rate_limit(user):
            return None
        token = self._deps.tokens.generate()
        await self._deps.reset_tokens.add(
            PasswordResetToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token_hash=self._deps.tokens.hash(token),
                expires_at=datetime.now(UTC) + _TOKEN_TTL,
            )
        )
        return self._build_mail(user, token, purpose)

    async def _over_rate_limit(self, user: User) -> bool:
        since = datetime.now(UTC) - _RATE_WINDOW
        recent = await self._deps.reset_tokens.count_created_since(user.id, since=since)
        return recent >= _MAX_TOKENS_PER_WINDOW

    def _build_mail(self, user: User, token: str, purpose: ResetPurpose) -> PendingMail:
        link = f"{self._deps.frontend_url}/reset-password?token={token}"
        if purpose == "activation":
            link += "&new=1"
        return PendingMail(
            to=user.email.value,
            subject=_SUBJECTS[purpose],
            body=_BODIES[purpose].format(link=link),
        )
