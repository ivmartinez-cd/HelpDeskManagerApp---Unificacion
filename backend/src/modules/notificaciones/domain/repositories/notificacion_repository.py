import uuid
from typing import Protocol

from src.modules.notificaciones.domain.entities.notificacion import (
    Notificacion,
    NuevaNotificacion,
)

# None = todas las audiencias (superadmin); si no, solo las que incluyen al usuario.
Audiencias = frozenset[str] | None


class PublicadorNotificaciones(Protocol):
    """Lo único que ven los otros módulos: publicar. Idempotente por `clave`.
    Escribe en la sesión del llamador — se confirma o se descarta junto con el
    resto de lo que haga ese ciclo/request."""

    async def publicar(self, notificaciones: list[NuevaNotificacion]) -> None: ...


class NotificacionRepository(PublicadorNotificaciones, Protocol):
    async def listar(
        self,
        usuario_id: uuid.UUID,
        audiencias: Audiencias,
        *,
        solo_no_leidas: bool,
        offset: int,
        limit: int,
    ) -> tuple[list[Notificacion], int]:
        """Más recientes primero. Devuelve (página, total que cumple el filtro)."""
        ...

    async def marcar_leidas(
        self, usuario_id: uuid.UUID, audiencias: Audiencias, ids: list[uuid.UUID] | None
    ) -> int:
        """Marca como leídas las indicadas (o todas si `ids` es None), solo entre
        las que el usuario puede ver. Devuelve cuántas pasaron a leídas."""
        ...
