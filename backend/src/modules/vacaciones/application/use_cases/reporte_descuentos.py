"""Reporte mensual de descuentos (discountedReport legacy): el jefe queda
clavado a su sector; el admin elige sector (default: el que se llame
'Técnico'). Sin sector resoluble devuelve vacío, como el legacy.
"""

import uuid
from calendar import monthrange
from dataclasses import dataclass
from datetime import date

from src.modules.vacaciones.application.dtos.ausencia_dtos import DescuentoRowDTO
from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.empleado import Empleado, EstadoEmpleado
from src.modules.vacaciones.domain.repositories.ausencia_repository import (
    AusenciaRepository,
)
from src.modules.vacaciones.domain.repositories.catalogos_repositories import (
    CargoRepository,
    SectorRepository,
)
from src.modules.vacaciones.domain.repositories.empleado_repository import (
    EmpleadoRepository,
    FiltrosEmpleados,
)
from src.modules.vacaciones.domain.repositories.feriado_repository import FeriadoRepository
from src.modules.vacaciones.domain.services.descuentos import (
    dias_corridos_en_mes,
    dias_descontados_en_mes,
)
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones

_SECTOR_DEFAULT = ("técnico", "tecnico")


@dataclass(frozen=True, slots=True)
class ReporteDescuentosDependencies:
    ausencias: AusenciaRepository
    empleados: EmpleadoRepository
    sectores: SectorRepository
    cargos: CargoRepository
    feriados: FeriadoRepository


class ReporteDescuentos:
    def __init__(self, deps: ReporteDescuentosDependencies) -> None:
        self._deps = deps

    async def execute(
        self,
        year: int,
        month: int,
        department_id: uuid.UUID | None,
        actor: ActorVacaciones,
    ) -> list[DescuentoRowDTO]:
        sector_id = await self._resolver_sector(department_id, actor)
        if sector_id is None:
            return []
        empleados = await self._deps.empleados.list_filtrados(
            FiltrosEmpleados(department_id=sector_id, status=EstadoEmpleado.ACTIVE)
        )
        if not empleados:
            return []
        inicio = date(year, month, 1)
        fin = date(year, month, monthrange(year, month)[1])
        feriados = frozenset(
            f.date for f in await self._deps.feriados.list_all() if inicio <= f.date <= fin
        )
        ausencias = await self._deps.ausencias.list_aprobadas_solapadas_de_empleados(
            [e.id for e in empleados], inicio, fin
        )
        cargos = {c.id: c.name for c in await self._deps.cargos.list_all()}
        return [
            self._fila(e, ausencias, cargos, year=year, month=month, feriados=feriados)
            for e in empleados
        ]

    async def _resolver_sector(
        self, department_id: uuid.UUID | None, actor: ActorVacaciones
    ) -> uuid.UUID | None:
        if actor.es_jefe_de_sector:
            return actor.sector_gestionado_id
        if department_id is not None:
            return department_id
        for sector in await self._deps.sectores.list_all():
            if sector.name.lower() in _SECTOR_DEFAULT:
                return sector.id
        return None

    def _fila(
        self,
        empleado: Empleado,
        ausencias: list[Ausencia],
        cargos: dict[uuid.UUID, str],
        *,
        year: int,
        month: int,
        feriados: frozenset[date],
    ) -> DescuentoRowDTO:
        propias = [a for a in ausencias if a.empleado_id == empleado.id]
        return DescuentoRowDTO(
            empleado_id=empleado.id,
            first_name=empleado.first_name,
            last_name=empleado.last_name,
            cargo_nombre=cargos.get(empleado.cargo_id, ""),
            dias_descontados=dias_descontados_en_mes(
                propias, year=year, month=month, feriados=feriados
            ),
            dias_enfermedad=dias_corridos_en_mes(
                propias, TipoAusencia.BAJA_ENFERMEDAD, year=year, month=month
            ),
            guardias=dias_corridos_en_mes(
                propias, TipoAusencia.GUARDIA, year=year, month=month
            ),
        )
