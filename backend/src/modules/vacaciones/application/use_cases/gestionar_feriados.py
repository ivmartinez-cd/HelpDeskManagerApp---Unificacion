import uuid
from dataclasses import dataclass

from src.modules.vacaciones.application.dtos.gestion_dtos import (
    FeriadoCommand,
    ImportFeriadosResultDTO,
)
from src.modules.vacaciones.domain.entities.feriado import Feriado
from src.modules.vacaciones.domain.errors import NombreDuplicadoError
from src.modules.vacaciones.domain.repositories.feriado_repository import FeriadoRepository
from src.modules.vacaciones.domain.repositories.feriados_externos import (
    FeriadosExternosProvider,
)
from src.shared.domain.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class GestionFeriadosDependencies:
    feriados: FeriadoRepository


class ListFeriados:
    def __init__(self, deps: GestionFeriadosDependencies) -> None:
        self._deps = deps

    async def execute(self) -> list[Feriado]:
        return await self._deps.feriados.list_all()


class CreateFeriado:
    def __init__(self, deps: GestionFeriadosDependencies) -> None:
        self._deps = deps

    async def execute(self, command: FeriadoCommand) -> Feriado:
        if await self._deps.feriados.get_by_date(command.fecha) is not None:
            raise NombreDuplicadoError("fecha", command.fecha.isoformat())
        feriado = Feriado(
            id=uuid.uuid4(),
            name=command.name,
            date=command.fecha,
            deducts_vacation=command.deducts_vacation,
        )
        await self._deps.feriados.add(feriado)
        return feriado


class UpdateFeriado:
    def __init__(self, deps: GestionFeriadosDependencies) -> None:
        self._deps = deps

    async def execute(self, feriado_id: uuid.UUID, command: FeriadoCommand) -> Feriado:
        feriado = await self._deps.feriados.get_by_id(feriado_id)
        if feriado is None:
            raise NotFoundError(f"Feriado {feriado_id} no encontrado")
        if command.fecha != feriado.date:
            existente = await self._deps.feriados.get_by_date(command.fecha)
            if existente is not None and existente.id != feriado_id:
                raise NombreDuplicadoError("fecha", command.fecha.isoformat())
        feriado.name = command.name
        feriado.date = command.fecha
        feriado.deducts_vacation = command.deducts_vacation
        await self._deps.feriados.save(feriado)
        return feriado


class DeleteFeriado:
    def __init__(self, deps: GestionFeriadosDependencies) -> None:
        self._deps = deps

    async def execute(self, feriado_id: uuid.UUID) -> None:
        if await self._deps.feriados.get_by_id(feriado_id) is None:
            raise NotFoundError(f"Feriado {feriado_id} no encontrado")
        await self._deps.feriados.delete(feriado_id)


@dataclass(frozen=True, slots=True)
class ImportarFeriadosDependencies:
    feriados: FeriadoRepository
    provider: FeriadosExternosProvider


class ImportarFeriados:
    """Import desde argentinadatos (paridad legacy): upsert por fecha, pisa el
    nombre y deja deducts_vacation=False."""

    def __init__(self, deps: ImportarFeriadosDependencies) -> None:
        self._deps = deps

    async def execute(self, year: int) -> ImportFeriadosResultDTO:
        importados = await self._deps.provider.fetch(year)
        for item in importados:
            await self._deps.feriados.upsert_por_fecha(
                Feriado(
                    id=uuid.uuid4(),
                    name=item.nombre,
                    date=item.fecha,
                    deducts_vacation=False,
                )
            )
        return ImportFeriadosResultDTO(year=year, count=len(importados))
