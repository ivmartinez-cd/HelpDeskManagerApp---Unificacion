"""Ciclo de vida de solicitudes: crear, editar, eliminar (orden de validación
exacto del legacy — ver validador_solicitud)."""

import uuid
from dataclasses import dataclass
from datetime import date

from src.modules.vacaciones.application.dtos.solicitud_dtos import (
    CrearSolicitudCommand,
    EditarSolicitudCommand,
)
from src.modules.vacaciones.application.use_cases.saldos_service import (
    SaldosDependencies,
    SaldosService,
)
from src.modules.vacaciones.application.use_cases.solicitud_datos import (
    aplicar_edicion,
    metadata_solicitud,
    nueva_solicitud,
    preparar_datos,
)
from src.modules.vacaciones.application.use_cases.solicitudes_context import (
    AgendaDependencies,
    cargar_agenda,
)
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.registro_auditoria import (
    ACCION_CREATE,
    ACCION_DELETE,
    ACCION_UPDATE,
    ENTIDAD_SOLICITUD,
)
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud
from src.modules.vacaciones.domain.errors import (
    EmpleadoNoEncontradoError,
    SolicitudNoEncontradaError,
    SoloPendientesEditablesError,
)
from src.modules.vacaciones.domain.repositories.auditoria import (
    RegistradorAuditoria,
    RegistradorAuditoriaNulo,
)
from src.modules.vacaciones.domain.repositories.catalogos_repositories import (
    CargoRepository,
    SectorRepository,
)
from src.modules.vacaciones.domain.repositories.ciclo_repository import CicloRepository
from src.modules.vacaciones.domain.repositories.clock import Clock
from src.modules.vacaciones.domain.repositories.config_repository import ConfigRepository
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.repositories.exclusion_repository import (
    ExclusionRepository,
)
from src.modules.vacaciones.domain.repositories.feriado_repository import FeriadoRepository
from src.modules.vacaciones.domain.repositories.notificador import (
    Notificador,
    NuevaSolicitudNotif,
)
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    RangoSolapado,
    SolicitudRepository,
)
from src.modules.vacaciones.domain.services.scoping import (
    verificar_puede_modificar_solicitud,
)
from src.modules.vacaciones.domain.services.validador_solicitud import (
    ContextoCreacion,
    ContextoEdicion,
    DatosSolicitud,
    validar_anio_objetivo,
    validar_creacion,
    validar_edicion,
)
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.shared.domain.errors import ValidationError


@dataclass(frozen=True, slots=True)
class SolicitudesDependencies:
    solicitudes: SolicitudRepository
    empleados: EmpleadoRepository
    sectores: SectorRepository
    cargos: CargoRepository
    ciclos: CicloRepository
    exclusiones: ExclusionRepository
    feriados: FeriadoRepository
    config: ConfigRepository
    clock: Clock
    notificador: Notificador
    auditoria: RegistradorAuditoria = RegistradorAuditoriaNulo()

    def saldos(self) -> SaldosService:
        return SaldosService(
            SaldosDependencies(
                empleados=self.empleados,
                ciclos=self.ciclos,
                solicitudes=self.solicitudes,
                config=self.config,
                clock=self.clock,
            )
        )

    def agenda(self) -> AgendaDependencies:
        return AgendaDependencies(
            solicitudes=self.solicitudes,
            exclusiones=self.exclusiones,
            empleados=self.empleados,
            cargos=self.cargos,
        )


class CrearSolicitud:
    def __init__(self, deps: SolicitudesDependencies) -> None:
        self._deps = deps

    async def execute(self, command: CrearSolicitudCommand, actor: ActorVacaciones) -> Solicitud:
        empleado = await self._resolver_empleado(command, actor)
        datos = await preparar_datos(self._deps.feriados, empleado, command)
        await self._validar_creacion(datos, actor)
        solicitud = nueva_solicitud(datos, command.reason)
        await self._deps.solicitudes.add(solicitud)
        await self._deps.auditoria.registrar(
            ACCION_CREATE,
            ENTIDAD_SOLICITUD,
            str(solicitud.id),
            metadata_solicitud(solicitud, empleado),
        )
        await self._notificar(empleado, solicitud)
        return solicitud

    async def _resolver_empleado(
        self, command: CrearSolicitudCommand, actor: ActorVacaciones
    ) -> Empleado:
        empleado_id = (
            command.empleado_id
            if actor.es_admin and command.empleado_id is not None
            else actor.empleado_id
        )
        if empleado_id is None:
            raise ValidationError("No se ha indicado el empleado")
        empleado = await self._deps.empleados.get_by_id(empleado_id)
        if empleado is None:
            raise EmpleadoNoEncontradoError(empleado_id)
        return empleado

    async def _validar_creacion(self, datos: DatosSolicitud, actor: ActorVacaciones) -> None:
        hoy = self._deps.clock.hoy()
        config = await self._deps.config.get()
        # Año primero (paridad legacy): un año inválido no debe crear ciclos.
        validar_anio_objetivo(datos.target_year, hoy=hoy, es_admin=actor.es_admin, config=config)
        rango = RangoSolapado(start=datos.start_date, end=datos.end_date)
        agenda = await cargar_agenda(self._deps.agenda(), datos.empleado, rango)
        saldo = await self._deps.saldos().saldo_de(datos.empleado, datos.target_year)
        ctx = ContextoCreacion(hoy=hoy, es_admin=actor.es_admin, config=config, saldo=saldo)
        validar_creacion(datos, agenda, ctx)

    async def _notificar(self, empleado: Empleado, solicitud: Solicitud) -> None:
        sector = await self._deps.sectores.get_by_id(empleado.department_id)
        await self._deps.notificador.notificar_nueva_solicitud(
            NuevaSolicitudNotif(
                empleado_nombre=empleado.nombre_completo,
                sector_nombre=sector.name if sector else "",
                department_id=empleado.department_id,
                start_date=solicitud.start_date,
                end_date=solicitud.end_date,
                dias=solicitud.days_requested,
                target_year=solicitud.anio_imputado,
                reason=solicitud.reason,
            )
        )


class EditarSolicitud:
    def __init__(self, deps: SolicitudesDependencies) -> None:
        self._deps = deps

    async def execute(
        self,
        solicitud_id: uuid.UUID,
        command: EditarSolicitudCommand,
        actor: ActorVacaciones,
    ) -> Solicitud:
        solicitud, empleado = await self._cargar_solicitud_y_empleado(solicitud_id, actor)
        # Paridad legacy: la edición NO re-valida año ni apertura de ciclo.
        datos = await preparar_datos(self._deps.feriados, empleado, command)
        await self._validar_edicion(solicitud, datos, actor)
        previo = (solicitud.start_date, solicitud.end_date)
        aplicar_edicion(solicitud, datos, command.reason)
        await self._deps.solicitudes.save(solicitud)
        await self._auditar_edicion(solicitud, empleado, previo)
        return solicitud

    async def _cargar_solicitud_y_empleado(
        self, solicitud_id: uuid.UUID, actor: ActorVacaciones
    ) -> tuple[Solicitud, Empleado]:
        solicitud = await self._deps.solicitudes.get_by_id(solicitud_id)
        if solicitud is None:
            raise SolicitudNoEncontradaError(solicitud_id)
        verificar_puede_modificar_solicitud(actor, solicitud.empleado_id)
        empleado = await self._deps.empleados.get_by_id(solicitud.empleado_id)
        if empleado is None:
            raise EmpleadoNoEncontradoError(solicitud.empleado_id)
        return solicitud, empleado

    async def _validar_edicion(
        self, solicitud: Solicitud, datos: DatosSolicitud, actor: ActorVacaciones
    ) -> None:
        rango = RangoSolapado(
            start=datos.start_date,
            end=datos.end_date,
            excluir_solicitud_id=solicitud.id,
        )
        agenda = await cargar_agenda(self._deps.agenda(), datos.empleado, rango)
        saldo = await self._deps.saldos().saldo_de(datos.empleado, datos.target_year)
        ctx = ContextoEdicion(
            es_admin=actor.es_admin,
            saldo=saldo,
            estado_actual=solicitud.status,
            dias_actuales=solicitud.days_requested,
        )
        validar_edicion(datos, agenda, ctx)

    async def _auditar_edicion(
        self, solicitud: Solicitud, empleado: Empleado, previo: tuple[date, date]
    ) -> None:
        metadata = metadata_solicitud(solicitud, empleado)
        metadata["previousStart"] = previo[0].isoformat()
        metadata["previousEnd"] = previo[1].isoformat()
        await self._deps.auditoria.registrar(
            ACCION_UPDATE, ENTIDAD_SOLICITUD, str(solicitud.id), metadata
        )


class EliminarSolicitud:
    def __init__(self, deps: SolicitudesDependencies) -> None:
        self._deps = deps

    async def execute(self, solicitud_id: uuid.UUID, actor: ActorVacaciones) -> None:
        solicitud = await self._deps.solicitudes.get_by_id(solicitud_id)
        if solicitud is None:
            raise SolicitudNoEncontradaError(solicitud_id)
        verificar_puede_modificar_solicitud(actor, solicitud.empleado_id)
        if not actor.es_admin and solicitud.status is not EstadoSolicitud.PENDING:
            raise SoloPendientesEditablesError("cancelar")
        empleado = await self._deps.empleados.get_by_id(solicitud.empleado_id)
        await self._deps.solicitudes.delete(solicitud_id)
        await self._deps.auditoria.registrar(
            ACCION_DELETE,
            ENTIDAD_SOLICITUD,
            str(solicitud.id),
            metadata_solicitud(solicitud, empleado),
        )
