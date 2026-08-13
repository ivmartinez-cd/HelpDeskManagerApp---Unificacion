"""Tests de integración de SqlAlchemyIncidenteRepository contra Postgres real."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    IncidenteEvaluado,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_incidente_repository import (  # noqa: E501
    SqlAlchemyIncidenteRepository,
)

from .conftest import incidente_importado


async def test_bulk_create_persists_all_and_returns_entities(
    db_session: AsyncSession, liquidacion_id: uuid.UUID
) -> None:
    repo = SqlAlchemyIncidenteRepository(db_session)

    creados = await repo.bulk_create(
        liquidacion_id,
        [
            incidente_importado(numero_incidente="INC-1"),
            incidente_importado(numero_incidente="INC-2"),
        ],
    )

    assert [i.numero_incidente for i in creados] == ["INC-1", "INC-2"]
    assert all(i.liquidacion_id == liquidacion_id for i in creados)


async def test_bulk_create_with_empty_sequence_returns_empty_list(
    db_session: AsyncSession, liquidacion_id: uuid.UUID
) -> None:
    resultado = await SqlAlchemyIncidenteRepository(db_session).bulk_create(liquidacion_id, [])

    assert resultado == []


async def test_list_by_liquidacion_returns_only_its_incidentes(
    db_session: AsyncSession, liquidacion_id: uuid.UUID, incidente_id: uuid.UUID
) -> None:
    resultado = await SqlAlchemyIncidenteRepository(db_session).list_by_liquidacion(
        liquidacion_id
    )

    assert [i.id for i in resultado] == [incidente_id]


async def test_list_by_prestador_joins_through_liquidacion(
    db_session: AsyncSession, prestador_id: uuid.UUID, incidente_id: uuid.UUID
) -> None:
    resultado = await SqlAlchemyIncidenteRepository(db_session).list_by_prestador(prestador_id)

    assert [i.id for i in resultado] == [incidente_id]


async def test_apply_evaluacion_updates_expected_fields(
    db_session: AsyncSession, incidente_id: uuid.UUID, liquidacion_id: uuid.UUID
) -> None:
    repo = SqlAlchemyIncidenteRepository(db_session)

    await repo.apply_evaluacion(
        [
            IncidenteEvaluado(
                incidente_id=incidente_id,
                costo_servicio_esperado=90.0,
                cant_km_esperado=8.0,
                costo_km_esperado=4.0,
                estado_validacion="alerta",
            )
        ]
    )

    fetched = (await repo.list_by_liquidacion(liquidacion_id))[0]
    assert fetched.costo_servicio_esperado == 90.0
    assert fetched.estado_validacion == "alerta"
