"""Link de activación por mail al dar acceso: mismo mail y mismo token que el
alta desde Usuarios (auth), despachado fuera del request."""

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.use_cases.request_password_reset import (
    RequestPasswordReset,
    RequestPasswordResetDependencies,
)
from src.modules.auth.infrastructure.mail_logo import get_logo_base64
from src.modules.auth.infrastructure.repositories.sqlalchemy_reset_token_repository import (
    SqlAlchemyResetTokenRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from src.modules.auth.infrastructure.secure_token_generator import SecureTokenGenerator
from src.modules.auth.presentation.password_mail import encolar_mail
from src.shared.infrastructure.config.settings import get_settings


class MailAvisoActivacion:
    def __init__(self, db: AsyncSession, background_tasks: BackgroundTasks) -> None:
        self._db = db
        self._background_tasks = background_tasks

    async def enviar(self, email: str) -> None:
        deps = RequestPasswordResetDependencies(
            users=SqlAlchemyUserRepository(self._db),
            reset_tokens=SqlAlchemyResetTokenRepository(self._db),
            tokens=SecureTokenGenerator(),
            frontend_url=get_settings().frontend_url,
            logo_base64=get_logo_base64(),
        )
        mail = await RequestPasswordReset(deps).execute(email, purpose="activation")
        encolar_mail(self._background_tasks, mail)
