import uuid
from dataclasses import dataclass

from src.modules.prestadores.application.dtos.prestador_dtos import AsignacionHistorialDTO
from src.modules.prestadores.domain.repositories.asignacion_historial_repository import (
    AsignacionHistorialRepository,
)
from src.modules.prestadores.domain.repositories.user_provider import UserProvider


@dataclass(frozen=True, slots=True)
class ListAsignacionHistorialDependencies:
    asignaciones: AsignacionHistorialRepository
    users: UserProvider


class ListAsignacionHistorial:
    """Caso de uso: historial de reasignación de operador de un PST, más
    reciente primero."""

    def __init__(self, deps: ListAsignacionHistorialDependencies) -> None:
        self._deps = deps

    async def execute(self, prestador_id: uuid.UUID) -> list[AsignacionHistorialDTO]:
        tramos = await self._deps.asignaciones.list_by_prestador(prestador_id)
        operador_ids = {t.operador_id for t in tramos if t.operador_id is not None}
        users = await self._deps.users.get_users_by_ids(list(operador_ids))
        return [
            AsignacionHistorialDTO(
                id=t.id,
                operador_id=t.operador_id,
                operador_nombre=users[t.operador_id].full_name
                if t.operador_id in users
                else None,
                desde=t.desde,
                hasta=t.hasta,
            )
            for t in sorted(tramos, key=lambda t: t.desde, reverse=True)
        ]
