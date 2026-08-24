from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from src.modules.bono_tecnicos.infrastructure.models.bono_tecnico_input_model import (
    BonoTecnicoInputModel,
)


def _row_to_entity(row: BonoTecnicoInputModel) -> BonoTecnicoInput:
    return BonoTecnicoInput(
        id_tecnico=row.id_tecnico,
        periodo=row.periodo,
        tecnico=row.tecnico,
        dias=row.dias,
        tareas_varias=row.tareas_varias,
    )


class SqlAlchemyBonoTecnicoInputRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_periodo(self, periodo: Periodo) -> list[BonoTecnicoInput]:
        stmt = select(BonoTecnicoInputModel).where(
            BonoTecnicoInputModel.periodo == periodo.value
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_row_to_entity(row) for row in rows]

    async def upsert(self, input_: BonoTecnicoInput) -> None:
        stmt = insert(BonoTecnicoInputModel).values(
            id_tecnico=input_.id_tecnico,
            periodo=input_.periodo,
            tecnico=input_.tecnico,
            dias=input_.dias,
            tareas_varias=input_.tareas_varias,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[BonoTecnicoInputModel.id_tecnico, BonoTecnicoInputModel.periodo],
            set_={
                "tecnico": stmt.excluded.tecnico,
                "dias": stmt.excluded.dias,
                "tareas_varias": stmt.excluded.tareas_varias,
                "updated_at": text("now()"),
            },
        )
        await self._session.execute(stmt)
