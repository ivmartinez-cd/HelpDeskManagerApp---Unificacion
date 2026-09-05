"""Verificación de existencia de usuarios referenciados por asignaciones,
coberturas y grillas de vacaciones. Sin esto la FK a `app_user` fallaba en
el flush y llegaba al cliente como 500."""

import uuid
from collections.abc import Iterable

from src.modules.turnos.domain.errors import UsuarioNotFoundError
from src.modules.turnos.domain.repositories.user_provider import UserProvider


async def validar_usuarios_existen(users: UserProvider, user_ids: Iterable[uuid.UUID]) -> None:
    ids = list(dict.fromkeys(user_ids))
    if not ids:
        return
    conocidos = await users.get_users_by_ids(ids)
    faltantes = [u for u in ids if u not in conocidos]
    if faltantes:
        raise UsuarioNotFoundError(faltantes)
