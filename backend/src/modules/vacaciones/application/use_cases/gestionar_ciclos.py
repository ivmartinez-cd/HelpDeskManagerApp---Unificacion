"""Ciclos anuales: listado admin, apertura manual del próximo año (paridad
openNextYearCycles) y saldo de un empleado (endpoint compartido por dashboard
y aprobaciones)."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.vacaciones.application.dtos.dashboard_dtos import (
    AbrirCiclosResultDTO,
    CicloDTO,
)
from src.modules.vacaciones.application.use_cases.saldos_service import (
    SaldosDependencies,
    SaldosService,
)
from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.domain.entities.empleado import EstadoEmpleado
from src.modules.vacaciones.domain.errors import (
    EmpleadoNoEncontradoError,
    OperacionNoPermitidaError,
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
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.modules.vacaciones.domain.value_objects.saldo import Saldo


@dataclass(frozen=True, slots=True)
class CiclosDependencies:
    ciclos: CicloRepository
    empleados: EmpleadoRepository
    solicitudes: SolicitudRepository
    config: ConfigRepository
    clock: Clock

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


class ListarCiclos:
    def __init__(self, deps: CiclosDependencies) -> None:
        self._deps = deps

    async def execute(self, year: int) -> list[CicloDTO]:
        ciclos = await self._deps.ciclos.list_por_year(year)
        empleados = await self._deps.empleados.get_by_ids([c.empleado_id for c in ciclos])
        return [
            CicloDTO(
                ciclo=c,
                empleado_nombre=(
                    empleados[c.empleado_id].nombre_completo
                    if c.empleado_id in empleados
                    else ""
                ),
            )
            for c in ciclos
        ]


class AbrirCiclosProximoAnio:
    """Apertura forzada manual (paridad openNextYearCycles): upsert del ciclo
    del año siguiente para todos los activos, con annual por antigüedad."""

    def __init__(self, deps: CiclosDependencies) -> None:
        self._deps = deps

    async def execute(self) -> AbrirCiclosResultDTO:
        next_year = self._deps.clock.hoy().year + 1
        config = await self._deps.config.get()
        activos = await self._deps.empleados.list_filtrados(
            FiltrosEmpleados(status=EstadoEmpleado.ACTIVE)
        )
        opened = 0
        skipped = 0
        for empleado in activos:
            annual = dias_por_antiguedad(
                empleado.hire_date, referencia_para_anio(next_year), config.seniority_tiers
            )
            existente = await self._deps.ciclos.get(empleado.id, next_year)
            if existente is not None and existente.is_open:
                skipped += 1
                continue
            if existente is None:
                await self._deps.ciclos.add(
                    Ciclo(
                        id=uuid.uuid4(),
                        empleado_id=empleado.id,
                        year=next_year,
                        annual_days=annual,
                        carry_over=0,
                        is_open=True,
                        opened_at=datetime.now(UTC),
                    )
                )
            else:
                existente.annual_days = annual
                existente.is_open = True
                existente.opened_at = datetime.now(UTC)
                await self._deps.ciclos.save(existente)
            opened += 1
        return AbrirCiclosResultDTO(opened=opened, skipped=skipped)


class ObtenerSaldoEmpleado:
    """Saldo de un empleado para un año. Acceso: el propio empleado, el jefe
    de su sector, o admin."""

    def __init__(self, deps: CiclosDependencies) -> None:
        self._deps = deps

    async def execute(
        self, empleado_id: uuid.UUID, year: int, actor: ActorVacaciones
    ) -> Saldo:
        empleado = await self._deps.empleados.get_by_id(empleado_id)
        if empleado is None:
            raise EmpleadoNoEncontradoError(empleado_id)
        es_propio = actor.empleado_id == empleado_id
        es_su_sector = actor.sector_gestionado_id == empleado.department_id
        if not (actor.es_admin or es_propio or es_su_sector):
            raise OperacionNoPermitidaError("No tenés acceso al saldo de este empleado")
        return await self._deps.saldos().saldo_de(empleado, year)
