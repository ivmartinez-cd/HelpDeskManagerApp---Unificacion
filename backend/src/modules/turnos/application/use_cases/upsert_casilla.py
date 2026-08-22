import uuid
from dataclasses import dataclass

from src.modules.turnos.application.dtos.turno_dtos import (
    CasillaDTO,
    CreateCasillaCommand,
    UpdateCasillaCommand,
)
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.errors import CasillaNotFoundError
from src.modules.turnos.domain.repositories.casilla_repository import CasillaRepository


@dataclass(frozen=True, slots=True)
class UpsertCasillaDependencies:
    casillas: CasillaRepository


class UpsertCasilla:
    """Caso de uso: crea o actualiza una casilla."""

    def __init__(self, deps: UpsertCasillaDependencies) -> None:
        self._deps = deps

    async def create(self, command: CreateCasillaCommand) -> CasillaDTO:
        casilla = Casilla(
            id=uuid.uuid4(),
            nombre=command.nombre,
            color=command.color,
            sort_order=command.sort_order,
            is_active=command.is_active,
        )
        await self._deps.casillas.add(casilla)
        return CasillaDTO(
            id=casilla.id,
            nombre=casilla.nombre,
            color=casilla.color,
            sort_order=casilla.sort_order,
            is_active=casilla.is_active,
        )

    async def update(self, command: UpdateCasillaCommand) -> CasillaDTO:
        existing = await self._deps.casillas.get_by_id(command.casilla_id)
        if existing is None:
            raise CasillaNotFoundError(command.casilla_id)

        casilla = Casilla(
            id=command.casilla_id,
            nombre=command.nombre,
            color=existing.color,
            sort_order=existing.sort_order,
            is_active=existing.is_active,
        )
        await self._deps.casillas.save(casilla)
        return CasillaDTO(
            id=casilla.id,
            nombre=casilla.nombre,
            color=casilla.color,
            sort_order=casilla.sort_order,
            is_active=casilla.is_active,
        )
