import uuid
from dataclasses import dataclass

from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.exclusion import Exclusion
from src.modules.vacaciones.domain.errors import NombreDuplicadoError
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.repositories.exclusion_repository import (
    ExclusionRepository,
)
from src.modules.vacaciones.domain.services.scoping import verificar_administra
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.shared.domain.errors import NotFoundError, ValidationError


@dataclass(frozen=True, slots=True)
class ExclusionConNombresDTO:
    exclusion: Exclusion
    empleado_a_nombre: str
    empleado_b_nombre: str


@dataclass(frozen=True, slots=True)
class ExclusionesDependencies:
    exclusiones: ExclusionRepository
    empleados: EmpleadoRepository


class ListarExclusiones:
    def __init__(self, deps: ExclusionesDependencies) -> None:
        self._deps = deps

    async def execute(self, actor: ActorVacaciones) -> list[ExclusionConNombresDTO]:
        """El admin con sector asignado ve solo las de dos personas de su sector."""
        exclusiones = await self._deps.exclusiones.list_all()
        ids = [e.empleado_a_id for e in exclusiones] + [e.empleado_b_id for e in exclusiones]
        nombres = await self._deps.empleados.get_by_ids(ids)
        if not actor.es_admin_global:
            exclusiones = _de_su_sector(exclusiones, nombres, actor)
        return [
            ExclusionConNombresDTO(
                exclusion=e,
                empleado_a_nombre=(
                    nombres[e.empleado_a_id].nombre_completo
                    if e.empleado_a_id in nombres
                    else ""
                ),
                empleado_b_nombre=(
                    nombres[e.empleado_b_id].nombre_completo
                    if e.empleado_b_id in nombres
                    else ""
                ),
            )
            for e in exclusiones
        ]


def _de_su_sector(
    exclusiones: list[Exclusion], empleados: dict[uuid.UUID, Empleado], actor: ActorVacaciones
) -> list[Exclusion]:
    return [
        e
        for e in exclusiones
        if all(
            i in empleados and actor.administra(empleados[i].department_id)
            for i in (e.empleado_a_id, e.empleado_b_id)
        )
    ]


class CrearExclusion:
    def __init__(self, deps: ExclusionesDependencies) -> None:
        self._deps = deps

    async def execute(
        self, empleado_a: uuid.UUID, empleado_b: uuid.UUID, actor: ActorVacaciones
    ) -> Exclusion:
        if empleado_a == empleado_b:
            raise ValidationError("Los dos empleados de la exclusión deben ser distintos")
        await _verificar_administra_ambos(self._deps, actor, empleado_a, empleado_b)
        a, b = sorted([empleado_a, empleado_b])
        for existente in await self._deps.exclusiones.list_por_empleado(a):
            if existente.contraparte_de(a) == b:
                raise NombreDuplicadoError("exclusión", f"{a} ↔ {b}")
        exclusion = Exclusion(id=uuid.uuid4(), empleado_a_id=a, empleado_b_id=b)
        await self._deps.exclusiones.add(exclusion)
        return exclusion


class EliminarExclusion:
    def __init__(self, deps: ExclusionesDependencies) -> None:
        self._deps = deps

    async def execute(self, exclusion_id: uuid.UUID, actor: ActorVacaciones) -> None:
        exclusion = await self._deps.exclusiones.get_by_id(exclusion_id)
        if exclusion is None:
            raise NotFoundError(f"Exclusión {exclusion_id} no encontrada")
        await _verificar_administra_ambos(
            self._deps, actor, exclusion.empleado_a_id, exclusion.empleado_b_id
        )
        await self._deps.exclusiones.delete(exclusion_id)


async def _verificar_administra_ambos(
    deps: ExclusionesDependencies, actor: ActorVacaciones, a: uuid.UUID, b: uuid.UUID
) -> None:
    empleados = await deps.empleados.get_by_ids([a, b])
    for empleado_id in (a, b):
        empleado = empleados.get(empleado_id)
        verificar_administra(actor, empleado.department_id if empleado else None)
