"""Alcance por sector: un jefe (sector asignado en Gestión de Personal) solo ve
y toca gente de su sector, tenga o no permisos de administrador (decisión de
Iván, 2026-10-09). Se aplica envolviendo el repositorio, así todos los casos de
uso que leen personas quedan acotados sin repetir el chequeo."""

import uuid
from dataclasses import replace

from src.modules.personas.domain.entities.persona import Persona
from src.modules.personas.domain.repositories.persona_repository import (
    FiltrosPersonas,
    OrdenPersonas,
    PersonaRepository,
)


class PersonasDelSector:
    """`PersonaRepository` acotado a `sector_id`; con None no filtra nada."""

    def __init__(self, base: PersonaRepository, sector_id: uuid.UUID | None) -> None:
        self._base = base
        self._sector_id = sector_id

    async def list_page(
        self, filtros: FiltrosPersonas, orden: OrdenPersonas, *, page: int, size: int
    ) -> tuple[list[Persona], int]:
        if self._sector_id is None:
            return await self._base.list_page(filtros, orden, page=page, size=size)
        if filtros.sector_id not in (None, self._sector_id):
            return [], 0
        acotados = replace(filtros, sector_id=self._sector_id)
        return await self._base.list_page(acotados, orden, page=page, size=size)

    async def get(self, persona_id: uuid.UUID) -> Persona | None:
        """Una persona de otro sector se trata como inexistente (404)."""
        persona = await self._base.get(persona_id)
        if persona is None or self._sector_id in (None, persona.sector_id):
            return persona
        return None
