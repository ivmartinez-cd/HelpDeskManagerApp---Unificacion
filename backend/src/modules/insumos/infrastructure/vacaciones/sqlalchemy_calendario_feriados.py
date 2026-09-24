"""Adapter cruzado hacia el módulo `vacaciones`: los feriados que el semáforo de Despachados
saltea al contar días hábiles son los cargados en el módulo Vacaciones (`vacaciones_feriado`).

Dependencia cross-module a propósito y solo en infrastructure (nunca en domain/application
de insumos), mismo criterio que `SqlAlchemyAusenciasLookup` de turnos y
`SqlAlchemyDiasSugeridosGateway` de bono_tecnicos. Lee la tabla directo porque el
repositorio de vacaciones no ofrece una consulta por rango de fechas.
"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.infrastructure.models.feriado_model import VacacionesFeriadoModel


class SqlAlchemyCalendarioFeriados:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def feriados_entre(self, desde: date, hasta: date) -> frozenset[date]:
        stmt = select(VacacionesFeriadoModel.date).where(
            VacacionesFeriadoModel.date >= desde, VacacionesFeriadoModel.date <= hasta
        )
        return frozenset((await self._session.execute(stmt)).scalars().all())
