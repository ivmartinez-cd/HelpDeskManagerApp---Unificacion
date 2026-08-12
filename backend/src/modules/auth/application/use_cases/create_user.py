import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.errors import EmailAlreadyRegisteredError
from src.modules.auth.domain.repositories.operador_color_lookup import OperadorColorLookup
from src.modules.auth.domain.repositories.user_repository import UserRepository
from src.modules.auth.domain.services.password_hasher import PasswordHasher
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.raw_password import RawPassword


@dataclass(frozen=True, slots=True)
class CreateUserDependencies:
    users: UserRepository
    hasher: PasswordHasher
    operador_colors: OperadorColorLookup


class CreateUser:
    def __init__(self, deps: CreateUserDependencies) -> None:
        self._deps = deps

    async def execute(self, *, email: str, full_name: str) -> User:
        normalized_email = Email(email)
        if await self._deps.users.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegisteredError()
        user = User(
            id=uuid.uuid4(),
            email=normalized_email,
            password_hash=self._deps.hasher.hash(RawPassword(_unusable_password())),
            full_name=full_name,
            is_active=True,
            is_superadmin=False,
            created_at=datetime.now(UTC),
            color=await self._deps.operador_colors.find_color_by_nombre(full_name),
        )
        await self._deps.users.add(user)
        return user


def _unusable_password() -> str:
    return f"{secrets.token_urlsafe(24)}Aa1!"
