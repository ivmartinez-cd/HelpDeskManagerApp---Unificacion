"""Cálculo de saldos con ensure lazy de ciclos y write-behind de carry-over.

Reemplaza al `ensureCycle`+`getBalanceForYear` del legacy: asegura los ciclos
del rango [2026..target] (creándolos con annual por antigüedad y apertura por
política), corre la cadena iterativa de saldos (D6) y persiste el carry-over
calculado cuando difiere del almacenado (write-behind, paridad legacy).
Trabaja en batch para servir dashboard/calendario sin N+1.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud
from src.modules.vacaciones.domain.repositories.ciclo_repository import CicloRepository
from src.modules.vacaciones.domain.repositories.clock import Clock
from src.modules.vacaciones.domain.repositories.config_repository import ConfigRepository
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    SolicitudRepository,
)
from src.modules.vacaciones.domain.services.antiguedad import (
    dias_por_antiguedad,
    referencia_para_anio,
)
from src.modules.vacaciones.domain.services.ciclo_policy import is_open_por_politica
from src.modules.vacaciones.domain.services.saldo_calculator import (
    ANIO_BASE_CARRY_OVER,
    ConsumoAnual,
    ReglasCarryOver,
    SaldoAnual,
    calcular_cadena_saldos,
)
from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones
from src.modules.vacaciones.domain.value_objects.saldo import Saldo


@dataclass(frozen=True, slots=True)
class SaldosDependencies:
    empleados: EmpleadoRepository
    ciclos: CicloRepository
    solicitudes: SolicitudRepository
    config: ConfigRepository
    clock: Clock


class SaldosService:
    def __init__(self, deps: SaldosDependencies) -> None:
        self._deps = deps

    async def saldo_de(self, empleado: Empleado, target_year: int) -> Saldo:
        saldos = await self.saldos_batch([empleado], target_year)
        return saldos[empleado.id]

    async def saldos_batch(
        self, empleados: list[Empleado], target_year: int
    ) -> dict[uuid.UUID, Saldo]:
        config = await self._deps.config.get()
        ids = [e.id for e in empleados]
        ciclos = await self._deps.ciclos.list_por_empleados(ids)
        solicitudes = await self._deps.solicitudes.list_activas_de_empleados(ids)
        resultado: dict[uuid.UUID, Saldo] = {}
        for empleado in empleados:
            propios = [c for c in ciclos if c.empleado_id == empleado.id]
            activas = [s for s in solicitudes if s.empleado_id == empleado.id]
            resultado[empleado.id] = await self._saldo_empleado(
                empleado, target_year, config, propios, activas
            )
        return resultado

    async def _saldo_empleado(
        self,
        empleado: Empleado,
        target_year: int,
        config: ConfigVacaciones,
        ciclos: list[Ciclo],
        activas: list[Solicitud],
    ) -> Saldo:
        por_anio = {c.year: c for c in ciclos}
        inicio = min(ANIO_BASE_CARRY_OVER, target_year)
        for year in range(inicio, target_year + 1):
            if year not in por_anio:
                por_anio[year] = await self._crear_ciclo(empleado, year, config)
            else:
                await self._abrir_si_corresponde(por_anio[year], config)
        consumo = _consumo_por_anio(activas)
        reglas = ReglasCarryOver(
            allow_carry_over=config.allow_carry_over,
            max_carry_over_days=config.max_carry_over_days,
        )
        annual = {y: por_anio[y].annual_days for y in range(inicio, target_year + 1)}
        cadena = calcular_cadena_saldos(target_year, annual, consumo, reglas)
        await self._persistir_carry(por_anio, cadena)
        objetivo = cadena[target_year]
        return Saldo(
            annual=objetivo.annual,
            carry_over=objetivo.carry_over,
            used=objetivo.used,
            pending=objetivo.pending,
            available=objetivo.available,
            cycle_open=por_anio[target_year].is_open,
        )

    async def _crear_ciclo(
        self, empleado: Empleado, year: int, config: ConfigVacaciones
    ) -> Ciclo:
        hoy = self._deps.clock.hoy()
        annual = dias_por_antiguedad(
            empleado.hire_date, referencia_para_anio(year), config.seniority_tiers
        )
        is_open = is_open_por_politica(year, hoy, config)
        ciclo = Ciclo(
            id=uuid.uuid4(),
            empleado_id=empleado.id,
            year=year,
            annual_days=annual,
            carry_over=0,
            is_open=is_open,
            opened_at=datetime.now(UTC) if is_open else None,
        )
        await self._deps.ciclos.add(ciclo)
        return ciclo

    async def _abrir_si_corresponde(self, ciclo: Ciclo, config: ConfigVacaciones) -> None:
        """Upgrade lazy del flag (D7): si la política ya habilita el año y el
        ciclo sigue cerrado, se abre y persiste."""
        hoy = self._deps.clock.hoy()
        if not ciclo.is_open and is_open_por_politica(ciclo.year, hoy, config):
            ciclo.is_open = True
            ciclo.opened_at = datetime.now(UTC)
            await self._deps.ciclos.save(ciclo)

    async def _persistir_carry(
        self, por_anio: dict[int, Ciclo], cadena: dict[int, SaldoAnual]
    ) -> None:
        for year, saldo in cadena.items():
            ciclo = por_anio.get(year)
            if ciclo is not None and ciclo.carry_over != saldo.carry_over:
                ciclo.carry_over = saldo.carry_over
                await self._deps.ciclos.save(ciclo)


def _consumo_por_anio(activas: list[Solicitud]) -> dict[int, ConsumoAnual]:
    usados: dict[int, int] = {}
    pendientes: dict[int, int] = {}
    for s in activas:
        anio = s.anio_imputado
        if s.status is EstadoSolicitud.APPROVED:
            usados[anio] = usados.get(anio, 0) + s.days_requested
        else:
            pendientes[anio] = pendientes.get(anio, 0) + s.days_requested
    anios = set(usados) | set(pendientes)
    return {
        a: ConsumoAnual(used=usados.get(a, 0), pending=pendientes.get(a, 0)) for a in anios
    }
