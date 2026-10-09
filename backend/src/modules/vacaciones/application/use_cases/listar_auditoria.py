"""Lectura paginada del log de auditoría, con el email del usuario actuante
resuelto en batch (los registros guardan solo el user_id)."""

from dataclasses import dataclass

from src.modules.vacaciones.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.vacaciones.domain.errors import OperacionNoPermitidaError
from src.modules.vacaciones.domain.repositories.auditoria import (
    ORDEN_POR_DEFECTO,
    AuditoriaRepository,
    FiltrosAuditoria,
    OrdenAuditoria,
)
from src.modules.vacaciones.domain.repositories.user_directory import UserDirectory
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones


@dataclass(frozen=True, slots=True)
class RegistroAuditoriaDTO:
    registro: RegistroAuditoria
    user_email: str | None


@dataclass(frozen=True, slots=True)
class ListarAuditoriaDependencies:
    auditoria: AuditoriaRepository
    users: UserDirectory


class ListarAuditoria:
    def __init__(self, deps: ListarAuditoriaDependencies) -> None:
        self._deps = deps

    async def execute(
        self,
        filtros: FiltrosAuditoria,
        *,
        actor: ActorVacaciones,
        page: int,
        size: int,
        orden: OrdenAuditoria = ORDEN_POR_DEFECTO,
    ) -> tuple[list[RegistroAuditoriaDTO], int]:
        # El log mezcla todos los sectores y no se puede acotar por persona:
        # el admin con sector asignado no lo ve.
        if not actor.es_admin_global:
            raise OperacionNoPermitidaError("La auditoría es solo para administradores generales")
        registros, total = await self._deps.auditoria.list_pagina(
            filtros, offset=(page - 1) * size, limit=size, orden=orden
        )
        return await self._con_email(registros), total

    async def _con_email(self, registros: list[RegistroAuditoria]) -> list[RegistroAuditoriaDTO]:
        users = await self._deps.users.get_by_ids(
            [r.user_id for r in registros if r.user_id is not None]
        )
        return [
            RegistroAuditoriaDTO(
                registro=r,
                user_email=users[r.user_id].email if r.user_id in users else None,
            )
            for r in registros
        ]
