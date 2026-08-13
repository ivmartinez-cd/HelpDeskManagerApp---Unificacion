"""Lecturas de solicitudes con scoping server-side y enriquecimiento batch
(empleado + sector + historial de aprobaciones, sin N+1)."""

import uuid
from dataclasses import dataclass

from src.modules.vacaciones.application.dtos.solicitud_dtos import (
    AprobacionDTO,
    ListarSolicitudesQuery,
    SolapamientosDTO,
    SolicitudDTO,
)
from src.modules.vacaciones.domain.entities.solicitud import Solicitud
from src.modules.vacaciones.domain.errors import (
    EmpleadoNoEncontradoError,
    SolicitudNoEncontradaError,
)
from src.modules.vacaciones.domain.repositories.aprobacion_repository import (
    AprobacionRepository,
)
from src.modules.vacaciones.domain.repositories.catalogos_repositories import (
    SectorRepository,
)
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    FiltrosSolicitudes,
    RangoSolapado,
    SolicitudRepository,
)
from src.modules.vacaciones.domain.repositories.user_directory import UserDirectory
from src.modules.vacaciones.domain.services.scoping import (
    DatosSolicitudAjena,
    alcance_para_listado,
    verificar_puede_ver_solapamientos,
    verificar_puede_ver_solicitud,
)
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones


@dataclass(frozen=True, slots=True)
class LeerSolicitudesDependencies:
    solicitudes: SolicitudRepository
    empleados: EmpleadoRepository
    sectores: SectorRepository
    aprobaciones: AprobacionRepository
    users: UserDirectory


class _Enriquecedor:
    def __init__(self, deps: LeerSolicitudesDependencies) -> None:
        self._deps = deps

    async def enriquecer(self, solicitudes: list[Solicitud]) -> list[SolicitudDTO]:
        empleados = await self._deps.empleados.get_by_ids(
            list({s.empleado_id for s in solicitudes})
        )
        sectores = {s.id: s for s in await self._deps.sectores.list_all()}
        aprobaciones = await self._deps.aprobaciones.list_por_solicitudes(
            [s.id for s in solicitudes]
        )
        approver_ids = [
            a.approver_user_id
            for items in aprobaciones.values()
            for a in items
            if a.approver_user_id is not None
        ]
        approvers = await self._deps.users.get_by_ids(approver_ids)
        return [
            self._dto(s, empleados, sectores, aprobaciones, approvers) for s in solicitudes
        ]

    def _dto(
        self,
        solicitud: Solicitud,
        empleados: dict,  # type: ignore[type-arg]
        sectores: dict,  # type: ignore[type-arg]
        aprobaciones: dict,  # type: ignore[type-arg]
        approvers: dict,  # type: ignore[type-arg]
    ) -> SolicitudDTO:
        empleado = empleados.get(solicitud.empleado_id)
        sector = sectores.get(empleado.department_id) if empleado else None
        return SolicitudDTO(
            solicitud=solicitud,
            empleado_nombre=empleado.nombre_completo if empleado else "",
            sector_nombre=sector.name if sector else "",
            sector_color=sector.color if sector else "#3b82f6",
            empleado_color=empleado.color if empleado else "#3b82f6",
            aprobaciones=[
                AprobacionDTO(
                    aprobacion=a,
                    approver_email=(
                        approvers[a.approver_user_id].email
                        if a.approver_user_id in approvers
                        else None
                    ),
                )
                for a in aprobaciones.get(solicitud.id, [])
            ],
        )


class ListarSolicitudes:
    def __init__(self, deps: LeerSolicitudesDependencies) -> None:
        self._deps = deps

    async def execute(
        self, query: ListarSolicitudesQuery, actor: ActorVacaciones
    ) -> list[SolicitudDTO]:
        alcance = alcance_para_listado(actor)
        if alcance.sin_acceso:
            return []
        filtros = FiltrosSolicitudes(
            status=query.status,
            empleado_id=alcance.empleado_id or query.empleado_id,
            department_id=alcance.department_id or query.department_id,
            desde=query.desde,
            hasta=query.hasta,
        )
        solicitudes = await self._deps.solicitudes.list_filtradas(filtros)
        return await _Enriquecedor(self._deps).enriquecer(solicitudes)


class ObtenerSolicitud:
    def __init__(self, deps: LeerSolicitudesDependencies) -> None:
        self._deps = deps

    async def execute(
        self, solicitud_id: uuid.UUID, actor: ActorVacaciones
    ) -> SolicitudDTO:
        solicitud = await self._deps.solicitudes.get_by_id(solicitud_id)
        if solicitud is None:
            raise SolicitudNoEncontradaError(solicitud_id)
        empleado = await self._deps.empleados.get_by_id(solicitud.empleado_id)
        if empleado is None:
            raise EmpleadoNoEncontradoError(solicitud.empleado_id)
        verificar_puede_ver_solicitud(
            actor,
            DatosSolicitudAjena(
                empleado_id=empleado.id, department_id=empleado.department_id
            ),
        )
        return (await _Enriquecedor(self._deps).enriquecer([solicitud]))[0]


class ListarSolapamientos:
    def __init__(self, deps: LeerSolicitudesDependencies) -> None:
        self._deps = deps

    async def execute(
        self, solicitud_id: uuid.UUID, actor: ActorVacaciones
    ) -> SolapamientosDTO:
        solicitud = await self._deps.solicitudes.get_by_id(solicitud_id)
        if solicitud is None:
            raise SolicitudNoEncontradaError(solicitud_id)
        empleado = await self._deps.empleados.get_by_id(solicitud.empleado_id)
        if empleado is None:
            raise EmpleadoNoEncontradoError(solicitud.empleado_id)
        verificar_puede_ver_solapamientos(
            actor,
            DatosSolicitudAjena(
                empleado_id=empleado.id, department_id=empleado.department_id
            ),
        )
        equipo = await self._deps.solicitudes.list_activas_solapadas_de_departamento(
            empleado.department_id,
            RangoSolapado(
                start=solicitud.start_date,
                end=solicitud.end_date,
                excluir_solicitud_id=solicitud.id,
            ),
        )
        team_size = await self._deps.empleados.count_activos_por_departamento(
            empleado.department_id
        )
        overlaps = await _Enriquecedor(self._deps).enriquecer(equipo)
        return SolapamientosDTO(overlaps=overlaps, team_size=team_size)
