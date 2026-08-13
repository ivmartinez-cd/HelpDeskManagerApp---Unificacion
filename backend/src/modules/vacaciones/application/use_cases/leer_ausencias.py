"""Lectura de bajas con scoping server-side (empleado: propias; jefe: su
sector; admin: todo — mismos alcances que las solicitudes) y enriquecimiento
batch de empleado + sector.
"""

from dataclasses import dataclass

from src.modules.vacaciones.application.dtos.ausencia_dtos import (
    AusenciaDTO,
    ListarAusenciasQuery,
)
from src.modules.vacaciones.domain.repositories.ausencia_repository import (
    AusenciaRepository,
    FiltrosAusencias,
)
from src.modules.vacaciones.domain.repositories.catalogos_repositories import (
    SectorRepository,
)
from src.modules.vacaciones.domain.repositories.empleado_repository import EmpleadoRepository
from src.modules.vacaciones.domain.services.scoping import alcance_para_listado
from src.modules.vacaciones.domain.value_objects.actor import ActorVacaciones

_COLOR_DEFAULT = "#3b82f6"


@dataclass(frozen=True, slots=True)
class LeerAusenciasDependencies:
    ausencias: AusenciaRepository
    empleados: EmpleadoRepository
    sectores: SectorRepository


class ListarAusencias:
    def __init__(self, deps: LeerAusenciasDependencies) -> None:
        self._deps = deps

    async def execute(
        self, query: ListarAusenciasQuery, actor: ActorVacaciones
    ) -> list[AusenciaDTO]:
        alcance = alcance_para_listado(actor)
        if alcance.sin_acceso:
            return []
        filtros = FiltrosAusencias(
            status=query.status,
            tipo=query.tipo,
            empleado_id=alcance.empleado_id or query.empleado_id,
            department_id=alcance.department_id,
            desde=query.desde,
            hasta=query.hasta,
        )
        ausencias = await self._deps.ausencias.list_filtradas(filtros)
        empleados = await self._deps.empleados.get_by_ids(
            list({a.empleado_id for a in ausencias})
        )
        sectores = {s.id: s for s in await self._deps.sectores.list_all()}
        dtos = []
        for ausencia in ausencias:
            empleado = empleados.get(ausencia.empleado_id)
            sector = sectores.get(empleado.department_id) if empleado else None
            dtos.append(
                AusenciaDTO(
                    ausencia=ausencia,
                    empleado_nombre=empleado.nombre_completo if empleado else "",
                    empleado_color=empleado.color if empleado else _COLOR_DEFAULT,
                    sector_nombre=sector.name if sector else "",
                    sector_color=sector.color if sector else _COLOR_DEFAULT,
                )
            )
        return dtos
