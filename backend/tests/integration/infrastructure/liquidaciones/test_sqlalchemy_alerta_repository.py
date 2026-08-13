"""Tests de integración de SqlAlchemyAlertaRepository contra Postgres real."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import AlertaGenerada
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)


def _alerta_generada(incidente_id: uuid.UUID, tipo_alerta: str = "ALT001") -> AlertaGenerada:
    return AlertaGenerada(
        incidente_id=incidente_id,
        tipo_alerta=tipo_alerta,
        descripcion="Descripción de alerta",
        riesgo=2.5,
        datos_contexto={"km_actual": 10.0},
    )


async def test_replace_for_liquidacion_creates_alertas(
    db_session: AsyncSession, liquidacion_id: uuid.UUID, incidente_id: uuid.UUID
) -> None:
    repo = SqlAlchemyAlertaRepository(db_session)

    creadas = await repo.replace_for_liquidacion(
        liquidacion_id, [_alerta_generada(incidente_id)]
    )

    assert len(creadas) == 1
    assert creadas[0].tipo_alerta == "ALT001"
    assert creadas[0].datos_contexto == {"km_actual": 10.0}


async def test_replace_for_liquidacion_discards_previous_alertas(
    db_session: AsyncSession, liquidacion_id: uuid.UUID, incidente_id: uuid.UUID
) -> None:
    repo = SqlAlchemyAlertaRepository(db_session)
    await repo.replace_for_liquidacion(
        liquidacion_id, [_alerta_generada(incidente_id, "ALT001")]
    )

    segunda_pasada = await repo.replace_for_liquidacion(
        liquidacion_id, [_alerta_generada(incidente_id, "ALT002")]
    )

    todas = await repo.list_by_liquidacion(liquidacion_id)
    assert [a.tipo_alerta for a in todas] == ["ALT002"]
    assert [a.tipo_alerta for a in segunda_pasada] == ["ALT002"]


async def test_replace_for_liquidacion_with_empty_sequence_clears_alertas(
    db_session: AsyncSession, liquidacion_id: uuid.UUID, incidente_id: uuid.UUID
) -> None:
    repo = SqlAlchemyAlertaRepository(db_session)
    await repo.replace_for_liquidacion(liquidacion_id, [_alerta_generada(incidente_id)])

    resultado = await repo.replace_for_liquidacion(liquidacion_id, [])

    assert resultado == []
    assert await repo.list_by_liquidacion(liquidacion_id) == []


async def test_list_by_liquidacion_returns_empty_when_none(
    db_session: AsyncSession, liquidacion_id: uuid.UUID
) -> None:
    assert await SqlAlchemyAlertaRepository(db_session).list_by_liquidacion(liquidacion_id) == []
