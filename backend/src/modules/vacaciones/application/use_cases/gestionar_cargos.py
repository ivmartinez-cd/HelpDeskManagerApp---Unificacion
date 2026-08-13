import uuid
from dataclasses import dataclass

from src.modules.vacaciones.application.dtos.gestion_dtos import CargoCommand, CargoDTO
from src.modules.vacaciones.domain.entities.cargo import Cargo
from src.modules.vacaciones.domain.entities.registro_auditoria import (
    ACCION_CREATE,
    ACCION_DELETE,
    ACCION_UPDATE,
    ENTIDAD_CARGO,
)
from src.modules.vacaciones.domain.errors import CargoConEmpleadosError, NombreDuplicadoError
from src.modules.vacaciones.domain.repositories.auditoria import (
    RegistradorAuditoria,
    RegistradorAuditoriaNulo,
)
from src.modules.vacaciones.domain.repositories.catalogos_repositories import CargoRepository
from src.shared.domain.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class GestionCargosDependencies:
    cargos: CargoRepository
    auditoria: RegistradorAuditoria = RegistradorAuditoriaNulo()


class ListCargos:
    def __init__(self, deps: GestionCargosDependencies) -> None:
        self._deps = deps

    async def execute(self) -> list[CargoDTO]:
        cargos = await self._deps.cargos.list_all()
        return [
            CargoDTO(cargo=c, empleados_count=await self._deps.cargos.count_empleados(c.id))
            for c in cargos
        ]


class CreateCargo:
    def __init__(self, deps: GestionCargosDependencies) -> None:
        self._deps = deps

    async def execute(self, command: CargoCommand) -> Cargo:
        if await self._deps.cargos.get_by_name(command.name) is not None:
            raise NombreDuplicadoError("nombre", command.name)
        cargo = Cargo(
            id=uuid.uuid4(), name=command.name, max_simultaneos=command.max_simultaneos
        )
        await self._deps.cargos.add(cargo)
        await self._deps.auditoria.registrar(
            ACCION_CREATE, ENTIDAD_CARGO, str(cargo.id), {"name": cargo.name}
        )
        return cargo


class UpdateCargo:
    def __init__(self, deps: GestionCargosDependencies) -> None:
        self._deps = deps

    async def execute(self, cargo_id: uuid.UUID, command: CargoCommand) -> Cargo:
        cargo = await self._deps.cargos.get_by_id(cargo_id)
        if cargo is None:
            raise NotFoundError(f"Cargo {cargo_id} no encontrado")
        if (
            command.name != cargo.name
            and await self._deps.cargos.get_by_name(command.name) is not None
        ):
            raise NombreDuplicadoError("nombre", command.name)
        cargo.name = command.name
        cargo.max_simultaneos = command.max_simultaneos
        await self._deps.cargos.save(cargo)
        await self._deps.auditoria.registrar(
            ACCION_UPDATE, ENTIDAD_CARGO, str(cargo.id), {"name": cargo.name}
        )
        return cargo


class DeleteCargo:
    def __init__(self, deps: GestionCargosDependencies) -> None:
        self._deps = deps

    async def execute(self, cargo_id: uuid.UUID) -> None:
        cargo = await self._deps.cargos.get_by_id(cargo_id)
        if cargo is None:
            raise NotFoundError(f"Cargo {cargo_id} no encontrado")
        if await self._deps.cargos.count_empleados(cargo_id) > 0:
            raise CargoConEmpleadosError()
        await self._deps.cargos.delete(cargo_id)
        await self._deps.auditoria.registrar(
            ACCION_DELETE, ENTIDAD_CARGO, str(cargo_id), {"name": cargo.name}
        )
