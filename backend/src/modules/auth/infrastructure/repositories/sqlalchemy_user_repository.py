import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.password_hash import PasswordHash
from src.modules.auth.infrastructure.models.user_model import AppUser


class SqlAlchemyUserRepository:
    """Implementa el puerto UserRepository. `add`/`save` hacen `flush`, no
    `commit` — el límite de transacción es responsabilidad de quien orquesta
    (use case / dependency de FastAPI), no del repositorio."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        model = await self._session.get(AppUser, user_id)
        return _to_entity(model) if model else None

    async def get_by_email(self, email: Email) -> User | None:
        stmt = select(AppUser).where(AppUser.email == email.value)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model else None

    async def add(self, user: User) -> None:
        self._session.add(_to_new_model(user))
        await self._session.flush()

    async def save(self, user: User) -> None:
        model = await self._session.get(AppUser, user.id)
        if model is None:
            raise LookupError(f"User {user.id} no existe")
        _apply_changes(model, user)
        await self._session.flush()


def _to_entity(model: AppUser) -> User:
    return User(
        id=model.id,
        email=Email(model.email),
        password_hash=PasswordHash(model.password_hash),
        full_name=model.full_name,
        is_active=model.is_active,
        is_superadmin=model.is_superadmin,
        created_at=model.created_at,
        last_login_at=model.last_login_at,
    )


def _to_new_model(user: User) -> AppUser:
    return AppUser(
        id=user.id,
        email=user.email.value,
        password_hash=user.password_hash.value,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superadmin=user.is_superadmin,
    )


def _apply_changes(model: AppUser, user: User) -> None:
    model.email = user.email.value
    model.password_hash = user.password_hash.value
    model.full_name = user.full_name
    model.is_active = user.is_active
    model.is_superadmin = user.is_superadmin
    model.last_login_at = user.last_login_at
