"""Armado del contexto de validación de solicitudes: carga los datos que el
validador puro necesita (solicitudes propias, exclusiones con nombres, límite
por cargo) con las mismas queries que el legacy."""

import uuid
from dataclasses import dataclass
from datetime import date

from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.repositories.catalogos_repositories import CargoRepository
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.repositories.exclusion_repository import (
    ExclusionRepository,
)
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    RangoSolapado,
    SolicitudRepository,
)
from src.modules.vacaciones.domain.services.validador_solicitud import ContextoAgenda


@dataclass(frozen=True, slots=True)
class AgendaDependencies:
    solicitudes: SolicitudRepository
    exclusiones: ExclusionRepository
    empleados: EmpleadoRepository
    cargos: CargoRepository


async def cargar_agenda(
    deps: AgendaDependencies,
    empleado: Empleado,
    rango: RangoSolapado,
) -> ContextoAgenda:
    propias = await deps.solicitudes.list_activas_de_empleado(
        empleado.id, excluir_solicitud_id=rango.excluir_solicitud_id
    )
    contrapartes, solicitudes_contrapartes = await _cargar_exclusiones(deps, empleado, rango)
    limite, nombre_cargo, rangos = await _cargar_limite_cargo(deps, empleado, rango)
    return ContextoAgenda(
        solicitudes_propias=tuple(propias),
        contrapartes=contrapartes,
        solicitudes_contrapartes=tuple(solicitudes_contrapartes),
        limite_cargo=limite,
        nombre_cargo=nombre_cargo,
        rangos_mismo_cargo=tuple(rangos),
    )


async def _cargar_exclusiones(
    deps: AgendaDependencies, empleado: Empleado, rango: RangoSolapado
) -> tuple[dict[uuid.UUID, str], list]:  # type: ignore[type-arg]
    exclusiones = await deps.exclusiones.list_por_empleado(empleado.id)
    ids = [
        contraparte
        for e in exclusiones
        if (contraparte := e.contraparte_de(empleado.id)) is not None
    ]
    if not ids:
        return {}, []
    nombres = await deps.empleados.get_by_ids(ids)
    contrapartes = {i: nombres[i].nombre_completo for i in ids if i in nombres}
    solapadas = await deps.solicitudes.list_activas_solapadas_de_empleados(ids, rango)
    return contrapartes, solapadas


async def _cargar_limite_cargo(
    deps: AgendaDependencies, empleado: Empleado, rango: RangoSolapado
) -> tuple[int | None, str, list[tuple[date, date]]]:
    cargo = await deps.cargos.get_by_id(empleado.cargo_id)
    if cargo is None or cargo.max_simultaneos is None:
        return None, cargo.name if cargo else "desconocida", []
    rangos = await deps.solicitudes.list_rangos_activos_por_cargo(
        empleado.cargo_id, empleado.id, rango
    )
    return cargo.max_simultaneos, cargo.name, rangos
