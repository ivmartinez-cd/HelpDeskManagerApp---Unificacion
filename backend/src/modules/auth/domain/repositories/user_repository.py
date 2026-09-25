import uuid
from typing import Literal, Protocol

from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects.email import Email

# Columnas de la tabla de usuarios por las que se puede ordenar la página.
CampoOrdenUsuarios = Literal["usuario", "rol", "estado"]


class UserRepository(Protocol):
    """`list_page`: `query` filtra por email o nombre y `orden` elige la
    columna (rol y estado por su etiqueta visible: "Administrador" antes que
    "Usuario", "Activo" antes que "Inactivo"; el nombre desempata). Devuelve
    (items, total) — el total es lo que arma la paginación en la respuesta."""

    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...
    async def get_by_email(self, email: Email) -> User | None: ...
    async def add(self, user: User) -> None: ...
    async def save(self, user: User) -> None: ...
    async def list_page(
        self,
        *,
        page: int,
        size: int,
        query: str | None,
        orden: CampoOrdenUsuarios = "usuario",
        descendente: bool = False,
    ) -> tuple[list[User], int]: ...
    async def count_active_superadmins(self) -> int: ...
