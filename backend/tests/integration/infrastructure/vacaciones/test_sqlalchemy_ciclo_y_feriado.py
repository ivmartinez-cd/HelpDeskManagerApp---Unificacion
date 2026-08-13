import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.feriado import Feriado
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_ciclo_repository import (
    SqlAlchemyCicloRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_feriado_repository import (
    SqlAlchemyFeriadoRepository,
)


def _ciclo(empleado_id: uuid.UUID, year: int) -> Ciclo:
    return Ciclo(
        id=uuid.uuid4(),
        empleado_id=empleado_id,
        year=year,
        annual_days=14,
        carry_over=0,
        is_open=True,
        opened_at=None,
    )


@pytest.mark.asyncio
async def test_ciclo_save_actualiza_carry_over(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemyCicloRepository(db_session)
    ciclo = _ciclo(empleado.id, 2026)
    await repo.add(ciclo)

    ciclo.carry_over = 5
    await repo.save(ciclo)

    leido = await repo.get(empleado.id, 2026)
    assert leido is not None
    assert leido.carry_over == 5


@pytest.mark.asyncio
async def test_ciclo_unico_por_empleado_y_anio(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemyCicloRepository(db_session)
    await repo.add(_ciclo(empleado.id, 2026))
    with pytest.raises(IntegrityError):
        await repo.add(_ciclo(empleado.id, 2026))


@pytest.mark.asyncio
async def test_feriado_upsert_por_fecha_pisa_el_nombre(db_session: AsyncSession) -> None:
    repo = SqlAlchemyFeriadoRepository(db_session)
    fecha = date(2026, 7, 9)
    await repo.upsert_por_fecha(
        Feriado(id=uuid.uuid4(), name="9 de Julio", date=fecha, deducts_vacation=False)
    )
    await repo.upsert_por_fecha(
        Feriado(
            id=uuid.uuid4(),
            name="Día de la Independencia",
            date=fecha,
            deducts_vacation=False,
        )
    )
    feriados = [f for f in await repo.list_all() if f.date == fecha]
    assert len(feriados) == 1
    assert feriados[0].name == "Día de la Independencia"


@pytest.mark.asyncio
async def test_existe_no_deduce_en_solo_para_deducts_false(db_session: AsyncSession) -> None:
    repo = SqlAlchemyFeriadoRepository(db_session)
    await repo.add(
        Feriado(id=uuid.uuid4(), name="Puente", date=date(2026, 8, 17), deducts_vacation=True)
    )
    await repo.add(
        Feriado(id=uuid.uuid4(), name="Navidad", date=date(2026, 12, 25), deducts_vacation=False)
    )
    assert await repo.existe_no_deduce_en(date(2026, 12, 25)) is True
    assert await repo.existe_no_deduce_en(date(2026, 8, 17)) is False
    assert await repo.existe_no_deduce_en(date(2026, 1, 1)) is False
