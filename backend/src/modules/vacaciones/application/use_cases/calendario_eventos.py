"""Eventos del calendario: vacaciones activas + feriados, con el "restante"
corrido del legacy (saldo que va quedando a medida que se consumen las
solicitudes del año, en orden de inicio).

"Activas" = PENDING + APPROVED a propósito (paridad legacy): la grilla del
frontend (`vacaciones-month-grid.tsx`) atenúa las PENDING por `status`, así
que no se filtran acá."""

import uuid
from dataclasses import dataclass
from datetime import date, timedelta

from src.modules.vacaciones.application.dtos.dashboard_dtos import EventoCalendarioDTO
from src.modules.vacaciones.application.use_cases.saldos_service import (
    SaldosDependencies,
    SaldosService,
)
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.solicitud import Solicitud
from src.modules.vacaciones.domain.repositories.catalogos_repositories import (
    SectorRepository,
)
from src.modules.vacaciones.domain.repositories.ciclo_repository import CicloRepository
from src.modules.vacaciones.domain.repositories.clock import Clock
from src.modules.vacaciones.domain.repositories.config_repository import ConfigRepository
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.repositories.feriado_repository import FeriadoRepository
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    SolicitudRepository,
)
from src.modules.vacaciones.domain.services.scoping import alcance_para_calendario
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones
from src.modules.vacaciones.domain.value_objects.saldo import Saldo

_COLOR_FERIADO = "#ef4444"


@dataclass(frozen=True, slots=True)
class CalendarioDependencies:
    solicitudes: SolicitudRepository
    empleados: EmpleadoRepository
    sectores: SectorRepository
    feriados: FeriadoRepository
    ciclos: CicloRepository
    config: ConfigRepository
    clock: Clock


class CalendarioEventos:
    def __init__(self, deps: CalendarioDependencies) -> None:
        self._deps = deps

    async def execute(
        self, desde: date | None, hasta: date | None, actor: ActorVacaciones
    ) -> list[EventoCalendarioDTO]:
        alcance = alcance_para_calendario(actor)
        visibles = await self._deps.solicitudes.list_activas_en_rango(
            desde, hasta, alcance.department_id
        )
        eventos = await self._eventos_vacaciones(visibles)
        eventos.extend(await self._eventos_feriados())
        return eventos

    async def _eventos_vacaciones(self, visibles: list[Solicitud]) -> list[EventoCalendarioDTO]:
        empleados = await self._deps.empleados.get_by_ids(list({s.empleado_id for s in visibles}))
        sectores = {s.id: s for s in await self._deps.sectores.list_all()}
        restantes = await self._restantes(visibles, empleados)
        eventos = []
        for s in visibles:
            empleado = empleados.get(s.empleado_id)
            if empleado is None:
                continue
            sector = sectores.get(empleado.department_id)
            sector_nombre = sector.name if sector else ""
            restante = restantes.get(s.id, 0)
            eventos.append(
                EventoCalendarioDTO(
                    id=str(s.id),
                    titulo=(
                        f"{empleado.nombre_completo} - {sector_nombre} "
                        f"({s.days_requested} d, {restante} rest.)"
                    ),
                    start=s.start_date,
                    end_exclusivo=s.end_date + timedelta(days=1),
                    tipo="vacation",
                    color=empleado.color,
                    border_color=sector.color if sector else None,
                    status=s.status.value,
                    empleado=empleado.nombre_completo,
                    sector=sector_nombre,
                    dias=s.days_requested,
                    restantes=restante,
                    reason=s.reason,
                )
            )
        return eventos

    async def _restantes(
        self, visibles: list[Solicitud], empleados: dict[uuid.UUID, Empleado]
    ) -> dict[uuid.UUID, int]:
        """Para cada solicitud visible: annual+carry del año imputado menos lo
        consumido por las solicitudes activas anteriores (inclusive) de ese
        empleado/año, en orden de inicio — paridad con el runningAvailable."""
        objetivos = {(s.empleado_id, s.anio_imputado) for s in visibles}
        saldos = await self._saldos_por_objetivo(objetivos, empleados)
        todas = await self._deps.solicitudes.list_activas_de_empleados(
            list({e for (e, _) in objetivos})
        )
        restantes: dict[uuid.UUID, int] = {}
        for s in visibles:
            clave = (s.empleado_id, s.anio_imputado)
            saldo = saldos.get(clave)
            running = (saldo.annual + saldo.carry_over) if saldo else 0
            for otra in todas:
                if otra.empleado_id != s.empleado_id or otra.anio_imputado != s.anio_imputado:
                    continue
                running -= otra.days_requested
                if otra.id == s.id:
                    break
            restantes[s.id] = running
        return restantes

    async def _saldos_por_objetivo(
        self,
        objetivos: set[tuple[uuid.UUID, int]],
        empleados: dict[uuid.UUID, Empleado],
    ) -> dict[tuple[uuid.UUID, int], Saldo]:
        service = SaldosService(
            SaldosDependencies(
                empleados=self._deps.empleados,
                ciclos=self._deps.ciclos,
                solicitudes=self._deps.solicitudes,
                config=self._deps.config,
                clock=self._deps.clock,
            )
        )
        saldos: dict[tuple[uuid.UUID, int], Saldo] = {}
        for year in {y for (_, y) in objetivos}:
            del_anio = [empleados[e] for (e, y) in objetivos if y == year and e in empleados]
            batch = await service.saldos_batch(del_anio, year)
            for e in batch:
                saldos[(e, year)] = batch[e]
        return saldos

    async def _eventos_feriados(self) -> list[EventoCalendarioDTO]:
        feriados = await self._deps.feriados.list_all()
        return [
            EventoCalendarioDTO(
                id=f"holiday-{f.id}",
                titulo=f.name,
                start=f.date,
                end_exclusivo=f.date + timedelta(days=1),
                tipo="holiday",
                color=_COLOR_FERIADO,
                border_color=None,
                status=None,
                empleado=None,
                sector=None,
                dias=None,
                restantes=None,
                reason=None,
            )
            for f in feriados
        ]
