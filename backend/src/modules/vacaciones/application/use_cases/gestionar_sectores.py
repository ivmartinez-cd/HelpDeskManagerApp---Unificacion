import uuid
from dataclasses import dataclass

from src.modules.vacaciones.application.dtos.gestion_dtos import SectorCommand, SectorDTO
from src.modules.vacaciones.domain.entities.sector import Sector
from src.modules.vacaciones.domain.errors import (
    NombreDuplicadoError,
    SectorConEmpleadosError,
)
from src.modules.vacaciones.domain.repositories.catalogos_repositories import SectorRepository
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.repositories.sector_manager_repository import (
    SectorManagerRepository,
)
from src.modules.vacaciones.domain.repositories.user_directory import UserDirectory
from src.shared.domain.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class GestionSectoresDependencies:
    sectores: SectorRepository
    empleados: EmpleadoRepository
    sector_manager: SectorManagerRepository
    users: UserDirectory


class ListSectores:
    def __init__(self, deps: GestionSectoresDependencies) -> None:
        self._deps = deps

    async def execute(self) -> list[SectorDTO]:
        sectores = await self._deps.sectores.list_all()
        jefes = await self._deps.sector_manager.list_jefes()
        usuarios = await self._deps.users.get_by_ids([j.user_id for j in jefes])
        dtos = []
        for sector in sectores:
            jefes_sector = [
                usuarios[j.user_id]
                for j in jefes
                if j.department_id == sector.id and j.user_id in usuarios
            ]
            count = await self._deps.empleados.count_activos_por_departamento(sector.id)
            dtos.append(SectorDTO(sector=sector, empleados_count=count, jefes=jefes_sector))
        return dtos


class CreateSector:
    def __init__(self, deps: GestionSectoresDependencies) -> None:
        self._deps = deps

    async def execute(self, command: SectorCommand) -> Sector:
        if await self._deps.sectores.get_by_name(command.name) is not None:
            raise NombreDuplicadoError("nombre", command.name)
        sector = Sector(
            id=uuid.uuid4(), name=command.name, color=command.color, is_active=True
        )
        await self._deps.sectores.add(sector)
        if command.jefe_user_id is not None:
            await self._deps.sector_manager.asignar(command.jefe_user_id, sector.id)
        return sector


class UpdateSector:
    def __init__(self, deps: GestionSectoresDependencies) -> None:
        self._deps = deps

    async def execute(self, sector_id: uuid.UUID, command: SectorCommand) -> Sector:
        sector = await self._deps.sectores.get_by_id(sector_id)
        if sector is None:
            raise NotFoundError(f"Sector {sector_id} no encontrado")
        if (
            command.name != sector.name
            and await self._deps.sectores.get_by_name(command.name) is not None
        ):
            raise NombreDuplicadoError("nombre", command.name)
        sector.name = command.name
        sector.color = command.color
        await self._deps.sectores.save(sector)
        await self._reasignar_jefe(sector_id, command.jefe_user_id)
        return sector

    async def _reasignar_jefe(
        self, sector_id: uuid.UUID, jefe_user_id: uuid.UUID | None
    ) -> None:
        """Un jefe por sector desde la UI: se desasignan los actuales del
        sector y se asigna el nuevo (si hay)."""
        for jefe in await self._deps.sector_manager.list_jefes():
            if jefe.department_id == sector_id and jefe.user_id != jefe_user_id:
                await self._deps.sector_manager.desasignar(jefe.user_id)
        if jefe_user_id is not None:
            await self._deps.sector_manager.asignar(jefe_user_id, sector_id)


class DeleteSector:
    def __init__(self, deps: GestionSectoresDependencies) -> None:
        self._deps = deps

    async def execute(self, sector_id: uuid.UUID) -> None:
        if await self._deps.sectores.get_by_id(sector_id) is None:
            raise NotFoundError(f"Sector {sector_id} no encontrado")
        if await self._deps.empleados.count_activos_por_departamento(sector_id) > 0:
            raise SectorConEmpleadosError()
        for jefe in await self._deps.sector_manager.list_jefes():
            if jefe.department_id == sector_id:
                await self._deps.sector_manager.desasignar(jefe.user_id)
        await self._deps.sectores.delete(sector_id)
