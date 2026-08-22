"""Tests de integración de SqlAlchemyResolucionRepository contra Postgres real."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.alerta import ESTADO_PENDIENTE
from src.modules.liquidaciones.domain.services.conciliar_alertas import AlertaConciliada
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import AlertaGenerada
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_resolucion_repository import (  # noqa: E501
    SqlAlchemyResolucionRepository,
)


async def _crear_alerta(
    db_session: AsyncSession, liquidacion_id: uuid.UUID, incidente_id: uuid.UUID
) -> uuid.UUID:
    creadas = await SqlAlchemyAlertaRepository(db_session).replace_for_liquidacion(
        liquidacion_id,
        [
            AlertaConciliada(
                generada=AlertaGenerada(
                    incidente_id=incidente_id,
                    tipo_alerta="ALT001",
                    descripcion="desc",
                    riesgo=1.0,
                    datos_contexto={},
                ),
                estado=ESTADO_PENDIENTE,
                justificacion=None,
            )
        ],
    )
    return creadas[0].id


async def test_create_then_list_by_alerta_round_trips(
    db_session: AsyncSession, liquidacion_id: uuid.UUID, incidente_id: uuid.UUID
) -> None:
    alerta_id = await _crear_alerta(db_session, liquidacion_id, incidente_id)
    repo = SqlAlchemyResolucionRepository(db_session)

    creada = await repo.create(
        alerta_id=alerta_id,
        decision="aprobado",
        justificacion="Verificado con el prestador",
        comentario=None,
    )

    resultado = await repo.list_by_alerta(alerta_id)
    assert [r.id for r in resultado] == [creada.id]
    assert resultado[0].decision == "aprobado"


async def test_list_by_alerta_returns_empty_when_none(db_session: AsyncSession) -> None:
    assert await SqlAlchemyResolucionRepository(db_session).list_by_alerta(uuid.uuid4()) == []
