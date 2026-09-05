"""Validación de referencias a otras entidades antes de escribir: un id que
no existe es un 404 de dominio, no una `ForeignKeyViolation` que sube como
500 (el handler central de `IntegrityError` queda como red de seguridad)."""

import uuid
from collections.abc import Iterable

from src.modules.prestadores.domain.errors import (
    OperadorNoEncontradoError,
    PrestadorNotFoundError,
)
from src.modules.prestadores.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.prestadores.domain.repositories.user_provider import UserInfo, UserProvider


async def exigir_operadores(
    users: UserProvider, operador_ids: Iterable[uuid.UUID | None]
) -> dict[uuid.UUID, UserInfo]:
    """Devuelve los usuarios encontrados (para armar el DTO sin otra consulta);
    falla con el primer id que no exista. `None` = "sin operador", se ignora."""
    ids = [i for i in dict.fromkeys(operador_ids) if i is not None]
    encontrados = await users.get_users_by_ids(ids)
    for operador_id in ids:
        if operador_id not in encontrados:
            raise OperadorNoEncontradoError(operador_id)
    return encontrados


async def exigir_prestadores(
    prestadores: PrestadorRepository, prestador_ids: Iterable[uuid.UUID]
) -> None:
    for prestador_id in dict.fromkeys(prestador_ids):
        if await prestadores.get_by_id(prestador_id) is None:
            raise PrestadorNotFoundError()
