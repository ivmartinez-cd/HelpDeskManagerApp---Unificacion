"""Lectura paginada del log de auditoría, con el email del usuario actuante
resuelto en batch (los registros guardan solo el user_id)."""

from dataclasses import dataclass

from src.modules.vacaciones.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.vacaciones.domain.repositories.auditoria import (
    AuditoriaRepository,
    FiltrosAuditoria,
)
from src.modules.vacaciones.domain.repositories.user_directory import UserDirectory


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
        self, filtros: FiltrosAuditoria, *, page: int, size: int
    ) -> tuple[list[RegistroAuditoriaDTO], int]:
        registros, total = await self._deps.auditoria.list_pagina(
            filtros, offset=(page - 1) * size, limit=size
        )
        users = await self._deps.users.get_by_ids(
            [r.user_id for r in registros if r.user_id is not None]
        )
        dtos = [
            RegistroAuditoriaDTO(
                registro=r,
                user_email=users[r.user_id].email if r.user_id in users else None,
            )
            for r in registros
        ]
        return dtos, total
