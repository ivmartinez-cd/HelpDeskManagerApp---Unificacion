"""Reporte de saldos por empleado y por sector (report.controller legacy).

Paridad: incluye TODOS los empleados (también inactivos), ordena empleados por
nombre y sectores por nombre, y usa el saldo del año en curso. `annual` es el
del ciclo (sin carry); `available` sí refleja el carry-over, igual que el
`getEmployeeBalance` legacy.
"""

import uuid
from dataclasses import dataclass

from src.modules.vacaciones.application.dtos.reporte_dtos import (
    FilaEmpleadoReporteDTO,
    FilaSectorReporteDTO,
    ReporteVacacionesDTO,
)
from src.modules.vacaciones.application.use_cases.saldos_service import (
    SaldosDependencies,
    SaldosService,
)
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.sector import Sector
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
from src.modules.vacaciones.domain.value_objects.saldo import Saldo


@dataclass(frozen=True, slots=True)
class ReporteVacacionesDependencies:
    empleados: EmpleadoRepository
    sectores: SectorRepository
    cargos: CargoRepository
    ciclos: CicloRepository
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


class ReporteVacaciones:
    def __init__(self, deps: ReporteVacacionesDependencies) -> None:
        self._deps = deps

    async def execute(self) -> ReporteVacacionesDTO:
        year = self._deps.clock.hoy().year
        empleados = await self._deps.empleados.list_filtrados(FiltrosEmpleados())
        empleados.sort(key=lambda e: (e.first_name.casefold(), e.last_name.casefold()))
        saldos = await self._deps.saldos().saldos_batch(empleados, year)
        sectores = sorted(await self._deps.sectores.list_all(), key=lambda s: s.name)
        cargos = {c.id: c.name for c in await self._deps.cargos.list_all()}
        return ReporteVacacionesDTO(
            year=year,
            por_empleado=_por_empleado(empleados, saldos, sectores, cargos),
            por_sector=_por_sector(empleados, saldos, sectores),
        )


def _por_empleado(
    empleados: list[Empleado],
    saldos: dict[uuid.UUID, Saldo],
    sectores: list[Sector],
    cargos: dict[uuid.UUID, str],
) -> list[FilaEmpleadoReporteDTO]:
    por_id = {s.id: s for s in sectores}
    return [
        FilaEmpleadoReporteDTO(
            nombre=e.nombre_completo,
            color=e.color,
            sector_nombre=por_id[e.department_id].name if e.department_id in por_id else "",
            cargo_nombre=cargos.get(e.cargo_id, ""),
            annual=saldos[e.id].annual,
            used=saldos[e.id].used,
            pending=saldos[e.id].pending,
            available=saldos[e.id].available,
        )
        for e in empleados
    ]


def _por_sector(
    empleados: list[Empleado],
    saldos: dict[uuid.UUID, Saldo],
    sectores: list[Sector],
) -> list[FilaSectorReporteDTO]:
    filas = []
    for sector in sectores:
        propios = [e for e in empleados if e.department_id == sector.id]
        filas.append(
            FilaSectorReporteDTO(
                nombre=sector.name,
                color=sector.color,
                empleados=len(propios),
                annual=sum(saldos[e.id].annual for e in propios),
                used=sum(saldos[e.id].used for e in propios),
                available=sum(saldos[e.id].available for e in propios),
            )
        )
    return filas
