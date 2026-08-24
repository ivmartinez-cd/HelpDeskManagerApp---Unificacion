"""SqlAlchemyBonoTecnicoInputRepository contra Postgres real: upsert por
(id_tecnico, periodo) y listado filtrado por período."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from src.modules.bono_tecnicos.infrastructure.repositories.sqlalchemy_bono_tecnico_input_repository import (  # noqa: E501
    SqlAlchemyBonoTecnicoInputRepository,
)


def _id_tecnico() -> int:
    return uuid.uuid4().int % 1_000_000_000


async def test_upsert_inserta_y_luego_actualiza_la_misma_fila(db_session: AsyncSession) -> None:
    repo = SqlAlchemyBonoTecnicoInputRepository(db_session)
    id_tecnico = _id_tecnico()
    periodo = Periodo(202605)
    assert await repo.find_by_periodo(periodo) == []

    await repo.upsert(
        BonoTecnicoInput(
            id_tecnico=id_tecnico, periodo=202605, tecnico="CD - Ana", dias=17, tareas_varias=25
        )
    )
    guardados = await repo.find_by_periodo(periodo)
    assert len(guardados) == 1
    assert guardados[0].dias == 17
    assert guardados[0].tareas_varias == 25

    await repo.upsert(
        BonoTecnicoInput(
            id_tecnico=id_tecnico, periodo=202605, tecnico="CD - Ana", dias=20, tareas_varias=30
        )
    )
    actualizado = await repo.find_by_periodo(periodo)
    assert len(actualizado) == 1
    assert actualizado[0].dias == 20
    assert actualizado[0].tareas_varias == 30


async def test_find_by_periodo_no_trae_otros_periodos(db_session: AsyncSession) -> None:
    repo = SqlAlchemyBonoTecnicoInputRepository(db_session)
    id_tecnico = _id_tecnico()
    await repo.upsert(
        BonoTecnicoInput(
            id_tecnico=id_tecnico, periodo=202605, tecnico="CD - Ana", dias=17, tareas_varias=25
        )
    )
    await repo.upsert(
        BonoTecnicoInput(
            id_tecnico=id_tecnico, periodo=202606, tecnico="CD - Ana", dias=18, tareas_varias=10
        )
    )

    solo_mayo = await repo.find_by_periodo(Periodo(202605))

    assert len(solo_mayo) == 1
    assert solo_mayo[0].periodo == 202605
    assert solo_mayo[0].dias == 17
