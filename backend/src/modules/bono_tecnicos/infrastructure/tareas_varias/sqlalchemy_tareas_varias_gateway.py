"""Adapter que cruza con las Tareas Varias del módulo `tareas_varias` —
dependencia cross-module a propósito, solo en infrastructure (nunca en
domain/application de bono_tecnicos), mismo criterio que
`infrastructure/vacaciones/sqlalchemy_dias_sugeridos_gateway.py`."""

from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.bono_tecnicos.domain.value_objects.conteo_tv import ConteoTv, ResumenTvTecnico
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from src.modules.tareas_varias.domain.entities.solicitud_tv import EstadoSolicitudTv
from src.modules.tareas_varias.domain.value_objects.periodo import Periodo as PeriodoTv
from src.modules.tareas_varias.infrastructure.repositories.sqlalchemy_solicitud_tv_repository import (  # noqa: E501
    SqlAlchemySolicitudTvRepository,
)


class SqlAlchemyTareasVariasGateway:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SqlAlchemySolicitudTvRepository(session)

    async def count_aprobadas_por_tecnico(self, periodo: Periodo) -> dict[int, int]:
        return await self._repo.count_aprobadas_por_tecnico(PeriodoTv(periodo.value))

    async def contar_por_tecnico_y_periodo(self, anio: int) -> dict[tuple[int, int], ConteoTv]:
        conteos = await self._repo.contar_por_tecnico_y_periodo(anio)
        return {
            clave: ConteoTv(solicitadas=c.solicitadas, aprobadas=c.aprobadas)
            for clave, c in conteos.items()
        }

    async def resumen_tecnico(self, periodo: Periodo, id_tecnico: int) -> ResumenTvTecnico:
        solicitudes = await self._repo.list_by_periodo(
            PeriodoTv(periodo.value), id_tecnico=id_tecnico
        )
        conteo = Counter(s.estado for s in solicitudes)
        return ResumenTvTecnico(
            aprobadas=conteo.get(EstadoSolicitudTv.APROBADA, 0),
            pendientes=conteo.get(EstadoSolicitudTv.PENDIENTE, 0),
            rechazadas=conteo.get(EstadoSolicitudTv.RECHAZADA, 0),
        )
