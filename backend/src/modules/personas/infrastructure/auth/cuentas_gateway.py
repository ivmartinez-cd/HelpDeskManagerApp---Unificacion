"""Escribe en las cuentas de acceso (auth) a través de sus casos de uso, para no
duplicar las reglas de alta, contraseña inutilizable y último superadmin
(ADR-040). Dependencia cross-module a propósito, solo en infrastructure."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.use_cases.create_user import CreateUser, CreateUserDependencies
from src.modules.auth.application.use_cases.update_user import UpdateUser, UpdateUserDependencies
from src.modules.auth.domain.errors import UserNotFoundError
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.well_known_permissions import MANAGE_ADMIN
from src.modules.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from src.modules.auth.infrastructure.repositories.sqlalchemy_permission_repository import (
    SqlAlchemyPermissionRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from src.modules.personas.domain.entities.persona import DatosPersona


class AuthCuentasGateway:
    def __init__(self, session: AsyncSession) -> None:
        self._users = SqlAlchemyUserRepository(session)
        self._permisos = SqlAlchemyPermissionRepository(session)

    async def email_en_uso(self, email: str, *, excepto: uuid.UUID | None) -> bool:
        cuenta = await self._users.get_by_email(Email(email))
        return cuenta is not None and cuenta.id != excepto

    async def es_privilegiada(self, user_id: uuid.UUID) -> bool:
        cuenta = await self._users.get_by_id(user_id)
        if cuenta is None:
            raise UserNotFoundError()
        if cuenta.is_superadmin:
            return True
        return (await self._permisos.get_for_user(user_id)).allows(MANAGE_ADMIN)

    async def actualizar_datos(self, user_id: uuid.UUID, datos: DatosPersona) -> None:
        cuenta = await self._users.get_by_id(user_id)
        if cuenta is None:
            raise UserNotFoundError()
        cuenta.full_name = datos.nombre_completo
        cuenta.email = Email(datos.email)
        cuenta.color = datos.color
        await self._users.save(cuenta)

    async def crear(self, datos: DatosPersona) -> uuid.UUID:
        deps = CreateUserDependencies(users=self._users, hasher=Argon2PasswordHasher())
        cuenta = await CreateUser(deps).execute(
            email=datos.email, full_name=datos.nombre_completo, color=datos.color
        )
        return cuenta.id

    async def activar(self, user_id: uuid.UUID) -> None:
        await self._cambiar_estado(user_id, activa=True)

    async def desactivar(self, user_id: uuid.UUID) -> None:
        await self._cambiar_estado(user_id, activa=False)

    async def _cambiar_estado(self, user_id: uuid.UUID, *, activa: bool) -> None:
        deps = UpdateUserDependencies(users=self._users)
        await UpdateUser(deps).execute(user_id=user_id, full_name=None, is_active=activa)
