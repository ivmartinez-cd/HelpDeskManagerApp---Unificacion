"""Escribe en las cuentas de acceso (auth) a través de sus casos de uso, para no
duplicar las reglas de alta, contraseña inutilizable y último superadmin
(ADR-040). Dependencia cross-module a propósito, solo en infrastructure."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.use_cases.create_user import CreateUser, CreateUserDependencies
from src.modules.auth.application.use_cases.update_user import UpdateUser, UpdateUserDependencies
from src.modules.auth.domain.errors import UserNotFoundError
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from src.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from src.modules.personas.domain.entities.persona import DatosPersona


class _SinColorDeOperador:
    """El color lo trae la persona: no se busca el de Gestión al crear la cuenta."""

    async def find_color_by_nombre(self, full_name: str) -> str | None:
        return None


class AuthCuentasGateway:
    def __init__(self, session: AsyncSession) -> None:
        self._users = SqlAlchemyUserRepository(session)

    async def email_en_uso(self, email: str, *, excepto: uuid.UUID | None) -> bool:
        cuenta = await self._users.get_by_email(Email(email))
        return cuenta is not None and cuenta.id != excepto

    async def actualizar_datos(self, user_id: uuid.UUID, datos: DatosPersona) -> None:
        cuenta = await self._users.get_by_id(user_id)
        if cuenta is None:
            raise UserNotFoundError()
        cuenta.full_name = datos.nombre_completo
        cuenta.email = Email(datos.email)
        cuenta.color = datos.color
        await self._users.save(cuenta)

    async def crear(self, datos: DatosPersona) -> uuid.UUID:
        deps = CreateUserDependencies(
            users=self._users, hasher=Argon2PasswordHasher(), operador_colors=_SinColorDeOperador()
        )
        cuenta = await CreateUser(deps).execute(email=datos.email, full_name=datos.nombre_completo)
        cuenta.color = datos.color
        await self._users.save(cuenta)
        return cuenta.id

    async def activar(self, user_id: uuid.UUID) -> None:
        await self._cambiar_estado(user_id, activa=True)

    async def desactivar(self, user_id: uuid.UUID) -> None:
        await self._cambiar_estado(user_id, activa=False)

    async def _cambiar_estado(self, user_id: uuid.UUID, *, activa: bool) -> None:
        deps = UpdateUserDependencies(users=self._users)
        await UpdateUser(deps).execute(user_id=user_id, full_name=None, is_active=activa)
