import uuid
from dataclasses import dataclass

from src.modules.vacaciones.application.dtos.gestion_dtos import (
    EmpleadoCommand,
    EmpleadoListItemDTO,
    ListEmpleadosQuery,
)
from src.modules.vacaciones.application.use_cases.saldos_service import (
    SaldosDependencies,
    SaldosService,
)
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.registro_auditoria import (
    ACCION_CREATE,
    ACCION_DELETE,
    ACCION_UPDATE,
    ENTIDAD_EMPLEADO,
)
from src.modules.vacaciones.domain.errors import (
    EmpleadoNoEncontradoError,
    NombreDuplicadoError,
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
from src.modules.vacaciones.domain.repositories.empleado_repository import (
    EmpleadoRepository,
    FiltrosEmpleados,
)
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    SolicitudRepository,
)
from src.modules.vacaciones.domain.services.antiguedad import (
    dias_por_antiguedad,
    referencia_para_anio,
)
from src.modules.vacaciones.domain.services.scoping import alcance_para_listado
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.shared.domain.errors import NotFoundError

_DIAS_POR_ANIO = 365.25


@dataclass(frozen=True, slots=True)
class GestionEmpleadosDependencies:
    empleados: EmpleadoRepository
    sectores: SectorRepository
    cargos: CargoRepository
    ciclos: CicloRepository
    config: ConfigRepository
    clock: Clock
    solicitudes: SolicitudRepository
    auditoria: RegistradorAuditoria = RegistradorAuditoriaNulo()


class ListEmpleados:
    def __init__(self, deps: GestionEmpleadosDependencies) -> None:
        self._deps = deps

    async def execute(
        self, query: ListEmpleadosQuery, actor: ActorVacaciones
    ) -> list[EmpleadoListItemDTO]:
        alcance = alcance_para_listado(actor)
        if alcance.sin_acceso:
            return []
        filtros = FiltrosEmpleados(
            search=query.search,
            department_id=alcance.department_id or query.department_id,
            status=query.status,
            empleado_id=alcance.empleado_id,
        )
        empleados = await self._deps.empleados.list_filtrados(filtros)
        return await self._enriquecer(empleados)

    async def _enriquecer(self, empleados: list[Empleado]) -> list[EmpleadoListItemDTO]:
        config = await self._deps.config.get()
        sectores = {s.id: s for s in await self._deps.sectores.list_all()}
        cargos = {c.id: c for c in await self._deps.cargos.list_all()}
        hoy = self._deps.clock.hoy()
        referencia = referencia_para_anio(hoy.year)

        saldos_service = SaldosService(
            SaldosDependencies(
                empleados=self._deps.empleados,
                ciclos=self._deps.ciclos,
                solicitudes=self._deps.solicitudes,
                config=self._deps.config,
                clock=self._deps.clock,
            )
        )
        saldos_anio = await saldos_service.saldos_batch(empleados, hoy.year)
        saldos_siguiente = await saldos_service.saldos_batch(empleados, hoy.year + 1)

        items = []
        for e in empleados:
            sector = sectores.get(e.department_id)
            cargo = cargos.get(e.cargo_id)
            saldo_siguiente = saldos_siguiente[e.id]
            items.append(
                EmpleadoListItemDTO(
                    empleado=e,
                    sector_nombre=sector.name if sector else "",
                    sector_color=sector.color if sector else "#3b82f6",
                    cargo_nombre=cargo.name if cargo else "",
                    dias_anuales=dias_por_antiguedad(
                        e.hire_date, referencia, config.seniority_tiers
                    ),
                    antiguedad_anios=(hoy - e.hire_date).days / _DIAS_POR_ANIO,
                    saldo=saldos_anio[e.id],
                    # Paridad con `nextYearBalance.cycleOpen ? … : null` del legacy.
                    saldo_siguiente=saldo_siguiente if saldo_siguiente.cycle_open else None,
                )
            )
        return items


class CreateEmpleado:
    def __init__(self, deps: GestionEmpleadosDependencies) -> None:
        self._deps = deps

    async def execute(self, command: EmpleadoCommand) -> Empleado:
        await _validar_referencias(self._deps, command)
        if await self._deps.empleados.get_by_email(command.email) is not None:
            raise NombreDuplicadoError("email", command.email)
        if command.user_id is not None:
            vinculado = await self._deps.empleados.get_by_user_id(command.user_id)
            if vinculado is not None:
                raise NombreDuplicadoError("usuario vinculado", str(command.user_id))
        empleado = _build_empleado(uuid.uuid4(), command)
        await self._deps.empleados.add(empleado)
        await self._deps.auditoria.registrar(
            ACCION_CREATE,
            ENTIDAD_EMPLEADO,
            str(empleado.id),
            {"employee": empleado.nombre_completo, "email": empleado.email},
        )
        return empleado


class UpdateEmpleado:
    def __init__(self, deps: GestionEmpleadosDependencies) -> None:
        self._deps = deps

    async def execute(self, empleado_id: uuid.UUID, command: EmpleadoCommand) -> Empleado:
        actual = await self._deps.empleados.get_by_id(empleado_id)
        if actual is None:
            raise EmpleadoNoEncontradoError(empleado_id)
        await _validar_referencias(self._deps, command)
        await self._validar_unicos(actual, command)
        if command.hire_date != actual.hire_date:
            await self._recalcular_ciclos(empleado_id, command)
        empleado = _build_empleado(empleado_id, command)
        await self._deps.empleados.save(empleado)
        await self._deps.auditoria.registrar(
            ACCION_UPDATE,
            ENTIDAD_EMPLEADO,
            str(empleado.id),
            {"employee": empleado.nombre_completo, "email": empleado.email},
        )
        return empleado

    async def _validar_unicos(self, actual: Empleado, command: EmpleadoCommand) -> None:
        if (
            command.email != actual.email
            and await self._deps.empleados.get_by_email(command.email) is not None
        ):
            raise NombreDuplicadoError("email", command.email)
        if command.user_id is not None and command.user_id != actual.user_id:
            vinculado = await self._deps.empleados.get_by_user_id(command.user_id)
            if vinculado is not None and vinculado.id != actual.id:
                raise NombreDuplicadoError("usuario vinculado", str(command.user_id))

    async def _recalcular_ciclos(
        self, empleado_id: uuid.UUID, command: EmpleadoCommand
    ) -> None:
        """Paridad con recalculateCyclesOnHireDateChange del legacy."""
        config = await self._deps.config.get()
        for ciclo in await self._deps.ciclos.list_por_empleado(empleado_id):
            annual = dias_por_antiguedad(
                command.hire_date, referencia_para_anio(ciclo.year), config.seniority_tiers
            )
            if annual != ciclo.annual_days:
                ciclo.annual_days = annual
                await self._deps.ciclos.save(ciclo)


class DeleteEmpleado:
    def __init__(self, deps: GestionEmpleadosDependencies) -> None:
        self._deps = deps

    async def execute(self, empleado_id: uuid.UUID) -> None:
        empleado = await self._deps.empleados.get_by_id(empleado_id)
        if empleado is None:
            raise EmpleadoNoEncontradoError(empleado_id)
        await self._deps.empleados.delete(empleado_id)
        await self._deps.auditoria.registrar(
            ACCION_DELETE,
            ENTIDAD_EMPLEADO,
            str(empleado_id),
            {"employee": empleado.nombre_completo, "email": empleado.email},
        )


async def _validar_referencias(
    deps: GestionEmpleadosDependencies, command: EmpleadoCommand
) -> None:
    if await deps.sectores.get_by_id(command.department_id) is None:
        raise NotFoundError(f"Sector {command.department_id} no encontrado")
    if await deps.cargos.get_by_id(command.cargo_id) is None:
        raise NotFoundError(f"Cargo {command.cargo_id} no encontrado")


def _build_empleado(empleado_id: uuid.UUID, command: EmpleadoCommand) -> Empleado:
    return Empleado(
        id=empleado_id,
        first_name=command.first_name,
        last_name=command.last_name,
        email=command.email,
        hire_date=command.hire_date,
        annual_vacation_days=22,
        status=command.status,
        color=command.color,
        department_id=command.department_id,
        cargo_id=command.cargo_id,
        user_id=command.user_id,
    )
