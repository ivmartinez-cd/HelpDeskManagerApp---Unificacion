"""Tests de integración de SqlAlchemyCalendarioFeriados (lee `vacaciones_feriado`)."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.repositories.consulta_despachos_repository import (
    CalendarioFeriados,
)
from src.modules.insumos.infrastructure.vacaciones.sqlalchemy_calendario_feriados import (
    SqlAlchemyCalendarioFeriados,
)
from src.modules.vacaciones.infrastructure.models.feriado_model import VacacionesFeriadoModel

FERIADOS = (date(2026, 10, 12), date(2026, 11, 20), date(2026, 12, 8), date(2026, 12, 25))


def _calendario(session: AsyncSession) -> CalendarioFeriados:
    return SqlAlchemyCalendarioFeriados(session)


async def _cargar_feriados(session: AsyncSession) -> None:
    session.add_all(VacacionesFeriadoModel(name=f"Feriado {dia}", date=dia) for dia in FERIADOS)
    await session.flush()


async def test_devuelve_los_feriados_del_rango_inclusive(db_session: AsyncSession) -> None:
    await _cargar_feriados(db_session)

    feriados = await _calendario(db_session).feriados_entre(date(2026, 10, 12), date(2026, 12, 8))

    assert feriados == frozenset({date(2026, 10, 12), date(2026, 11, 20), date(2026, 12, 8)})


async def test_un_solo_dia(db_session: AsyncSession) -> None:
    await _cargar_feriados(db_session)

    feriados = await _calendario(db_session).feriados_entre(date(2026, 12, 25), date(2026, 12, 25))

    assert feriados == frozenset({date(2026, 12, 25)})


async def test_rango_sin_feriados_o_invertido_devuelve_vacio(db_session: AsyncSession) -> None:
    await _cargar_feriados(db_session)

    assert await _calendario(db_session).feriados_entre(date(2026, 9, 1), date(2026, 9, 30)) == (
        frozenset()
    )
    assert await _calendario(db_session).feriados_entre(date(2026, 12, 31), date(2026, 1, 1)) == (
        frozenset()
    )
