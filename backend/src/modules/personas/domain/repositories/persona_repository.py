import uuid
from dataclasses import dataclass
from typing import Literal, Protocol

from src.modules.personas.domain.entities.persona import Persona

CampoOrdenPersonas = Literal["nombre", "email", "sector", "cargo", "acceso", "estado"]


@dataclass(frozen=True, slots=True)
class FiltrosPersonas:
    busqueda: str | None = None
    sector_id: uuid.UUID | None = None
    activa: bool | None = None
    entra_a_la_app: bool | None = None


@dataclass(frozen=True, slots=True)
class OrdenPersonas:
    campo: CampoOrdenPersonas = "nombre"
    descendente: bool = False


class PersonaRepository(Protocol):
    async def list_page(
        self, filtros: FiltrosPersonas, orden: OrdenPersonas, *, page: int, size: int
    ) -> tuple[list[Persona], int]: ...

    async def get(self, persona_id: uuid.UUID) -> Persona | None: ...
