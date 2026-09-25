import uuid

from src.modules.personas.domain.entities.persona import Persona
from src.modules.personas.domain.errors import PersonaNoEncontradaError
from src.modules.personas.domain.repositories.persona_repository import (
    FiltrosPersonas,
    OrdenPersonas,
    PersonaRepository,
)


class ListarPersonas:
    def __init__(self, personas: PersonaRepository) -> None:
        self._personas = personas

    async def execute(
        self, filtros: FiltrosPersonas, orden: OrdenPersonas, *, page: int, size: int
    ) -> tuple[list[Persona], int]:
        return await self._personas.list_page(filtros, orden, page=page, size=size)


class ObtenerPersona:
    def __init__(self, personas: PersonaRepository) -> None:
        self._personas = personas

    async def execute(self, persona_id: uuid.UUID) -> Persona:
        persona = await self._personas.get(persona_id)
        if persona is None:
            raise PersonaNoEncontradaError(persona_id)
        return persona
