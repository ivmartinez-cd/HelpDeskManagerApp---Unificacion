from datetime import datetime
from typing import Protocol

from src.modules.auth.domain.entities.password_reset_token import PasswordResetToken


class ResetTokenRepository(Protocol):
    """Devuelve el registro entero (no un `bool`/`None` colapsado): el caso
    de uso necesita distinguir "no existe" de "ya usado" de "vencido" para
    responder el código de error correcto (TOKEN_INVALID/ALREADY_USED/
    EXPIRED) — una corrección al diseño original de la Etapa 5."""

    async def add(self, token: PasswordResetToken) -> None: ...
    async def get_by_token_hash(self, token_hash: bytes) -> PasswordResetToken | None: ...
    async def mark_used(self, token_hash: bytes, *, at: datetime) -> None: ...
