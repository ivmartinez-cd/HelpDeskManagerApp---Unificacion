import uuid
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
    async def mark_used(self, token_hash: bytes, *, at: datetime) -> bool:
        """Quema el token si seguía sin usar; False si otro request ya lo usó
        (atómico: dos resets en paralelo con el mismo link no pasan los dos)."""
        ...

    async def mark_all_used_for_user(self, user_id: uuid.UUID, *, at: datetime) -> None:
        """Quema los otros links pendientes del usuario."""
        ...

    async def count_created_since(self, user_id: uuid.UUID, *, since: datetime) -> int:
        """Tokens emitidos al usuario desde `since` (usados o no): base del
        límite de frecuencia de /password/forgot."""
        ...
