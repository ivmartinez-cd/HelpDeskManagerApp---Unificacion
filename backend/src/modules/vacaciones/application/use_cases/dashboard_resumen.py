"""Resumen del dashboard, variante por actor (paridad con el legacy):
- admin: métricas globales + suma de saldos del equipo activo (batch, sin N+1)
- jefe: métricas de su sector + saldo propio si tiene empleado vinculado
- empleado: contadores globales (quirk legacy) + saldo propio.
"""

import uuid
from dataclasses import dataclass

from src.modules.vacaciones.application.dtos.dashboard_dtos import (
    DashboardResumenDTO,
    DiasDTO,
    EnVacacionesDTO,
)
from src.modules.vacaciones.application.use_cases.saldos_service import (
    SaldosDependencies,
    SaldosService,
)
from src.modules.vacaciones.domain.entities.empleado import Empleado, EstadoEmpleado
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.repositories.catalogos_repositories import (
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
    FiltrosSolicitudes,
    SolicitudRepository,
)
from src.modules.vacaciones.domain.services.ciclo_policy import is_open_por_politica
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones


@dataclass(frozen=True, slots=True)
class DashboardDependencies:
    empleados: EmpleadoRepository
    solicitudes: SolicitudRepository
    sectores: SectorRepository
    ciclos: CicloRepository
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


class DashboardResumen:
    def __init__(self, deps: DashboardDependencies) -> None:
        self._deps = deps

    async def execute(self, actor: ActorVacaciones) -> DashboardResumenDTO:
        sector_filtro = actor.sector_gestionado_id if actor.es_jefe_de_sector else None
        empleados = await self._deps.empleados.list_filtrados(
            FiltrosEmpleados(department_id=sector_filtro)
        )
        activos = [e for e in empleados if e.status is EstadoEmpleado.ACTIVE]
        pendientes = await self._deps.solicitudes.list_filtradas(
            FiltrosSolicitudes(status=EstadoSolicitud.PENDING, department_id=sector_filtro)
        )
        en_vacaciones = await self._en_vacaciones(sector_filtro)
        dias, dias_proximo = await self._dias_propios(actor)
        equipo_total, equipo_disponible = await self._saldos_equipo(actor, activos)
        return DashboardResumenDTO(
            total_empleados=len(empleados),
            empleados_activos=len(activos),
            solicitudes_pendientes=len(pendientes),
            en_vacaciones=en_vacaciones,
            dias=dias,
            dias_proximo=dias_proximo,
            dias_totales_equipo=equipo_total,
            dias_disponibles_equipo=equipo_disponible,
        )

    async def _en_vacaciones(
        self, sector_filtro: uuid.UUID | None
    ) -> list[EnVacacionesDTO]:
        hoy = self._deps.clock.hoy()
        cubren_hoy = [
            s
            for s in await self._deps.solicitudes.list_activas_en_rango(
                None, hoy, sector_filtro
            )
            if s.status is EstadoSolicitud.APPROVED and s.end_date >= hoy
        ]
        empleados = await self._deps.empleados.get_by_ids(
            list({s.empleado_id for s in cubren_hoy})
        )
        sectores = {s.id: s for s in await self._deps.sectores.list_all()}
        resultado = []
        for s in cubren_hoy:
            empleado = empleados.get(s.empleado_id)
            if empleado is None:
                continue
            sector = sectores.get(empleado.department_id)
            resultado.append(
                EnVacacionesDTO(
                    solicitud_id=s.id,
                    empleado_nombre=empleado.nombre_completo,
                    empleado_color=empleado.color,
                    sector_nombre=sector.name if sector else "",
                    sector_color=sector.color if sector else "#3b82f6",
                    start_date=s.start_date,
                    end_date=s.end_date,
                )
            )
        return resultado

    async def _dias_propios(
        self, actor: ActorVacaciones
    ) -> tuple[DiasDTO | None, DiasDTO | None]:
        if actor.empleado_id is None:
            return None, None
        empleado = await self._deps.empleados.get_by_id(actor.empleado_id)
        if empleado is None:
            return None, None
        hoy = self._deps.clock.hoy()
        service = self._deps.saldos()
        saldo = await service.saldo_de(empleado, hoy.year)
        dias = DiasDTO(saldo=saldo, year=hoy.year)
        config = await self._deps.config.get()
        proximo = None
        if is_open_por_politica(hoy.year + 1, hoy, config):
            saldo_prox = await service.saldo_de(empleado, hoy.year + 1)
            proximo = DiasDTO(saldo=saldo_prox, year=hoy.year + 1)
        return dias, proximo

    async def _saldos_equipo(
        self, actor: ActorVacaciones, activos: list[Empleado]
    ) -> tuple[int | None, int | None]:
        if not actor.es_admin or not activos:
            return None, None
        hoy = self._deps.clock.hoy()
        saldos = await self._deps.saldos().saldos_batch(activos, hoy.year)
        total = sum(s.annual + s.carry_over for s in saldos.values())
        disponible = sum(s.available for s in saldos.values())
        return total, disponible
