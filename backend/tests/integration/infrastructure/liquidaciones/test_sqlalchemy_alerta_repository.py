"""Tests de integración de SqlAlchemyAlertaRepository contra Postgres real."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.entities.alerta import ESTADO_PENDIENTE
from src.modules.liquidaciones.domain.services.conciliar_alertas import AlertaConciliada
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import AlertaGenerada
from src.modules.liquidaciones.infrastructure.models.alerta_model import AlertaIncidenteModel
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_incidente_repository import (  # noqa: E501
    SqlAlchemyIncidenteRepository,
)

from .conftest import incidente_importado


def _alerta_generada(incidente_id: uuid.UUID, tipo_alerta: str = "ALT001") -> AlertaConciliada:
    """El repo recibe la alerta ya conciliada con la decisión previa de la TL
    (ADR-024); acá siempre es una alerta nueva: estado pendiente, sin justificación."""
    generada = AlertaGenerada(
        incidente_id=incidente_id,
        tipo_alerta=tipo_alerta,
        descripcion="Descripción de alerta",
        riesgo=2.5,
        datos_contexto={"km_actual": 10.0},
    )
    return AlertaConciliada(generada=generada, estado=ESTADO_PENDIENTE, justificacion=None)


def _alerta_grupo_generada(principal: uuid.UUID, referencia: uuid.UUID) -> AlertaConciliada:
    """Ex `ObservacionGenerada` — hoy es una `AlertaGenerada` con es_grupo=True."""
    generada = AlertaGenerada(
        incidente_id=principal,
        tipo_alerta="ALT005",
        descripcion="Ruta compartida",
        riesgo=0.0,
        datos_contexto={"corredor": "AMBA"},
        es_grupo=True,
        grupo_incidente_ids=(principal, referencia),
        monto_cobrado=100.0,
        monto_esperado=80.0,
        diferencia=20.0,
    )
    return AlertaConciliada(generada=generada, estado=ESTADO_PENDIENTE, justificacion=None)


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


async def test_replace_for_liquidacion_creates_alerta_grupo_con_vinculos(
    db_session: AsyncSession, liquidacion_id: uuid.UUID
) -> None:
    creados = await SqlAlchemyIncidenteRepository(db_session).bulk_create(
        liquidacion_id,
        [
            incidente_importado(numero_incidente="INC-A"),
            incidente_importado(numero_incidente="INC-B"),
        ],
    )
    principal, referencia = creados[0].id, creados[1].id
    repo = SqlAlchemyAlertaRepository(db_session)

    creadas = await repo.replace_for_liquidacion(
        liquidacion_id, [_alerta_grupo_generada(principal, referencia)]
    )

    assert len(creadas) == 1
    assert creadas[0].es_grupo is True
    assert creadas[0].diferencia == 20.0
    assert set(creadas[0].grupo_incidente_ids) == {principal, referencia}
    vinculos = (
        await db_session.execute(
            select(AlertaIncidenteModel).where(AlertaIncidenteModel.alerta_id == creadas[0].id)
        )
    ).scalars().all()
    roles = {v.incidente_id: v.rol for v in vinculos}
    assert roles[principal] == "principal"
    assert roles[referencia] == "referencia"


async def test_update_estado_changes_estado(
    db_session: AsyncSession, liquidacion_id: uuid.UUID, incidente_id: uuid.UUID
) -> None:
    repo = SqlAlchemyAlertaRepository(db_session)
    creadas = await repo.replace_for_liquidacion(liquidacion_id, [_alerta_generada(incidente_id)])
    creada = creadas[0]

    actualizada = await repo.update_estado(
        liquidacion_id, creada.id, estado="revisada", justificacion="Ok, validado"
    )

    assert actualizada is not None
    assert actualizada.estado == "revisada"
    assert actualizada.justificacion == "Ok, validado"


async def test_update_estado_returns_none_when_liquidacion_no_coincide(
    db_session: AsyncSession, liquidacion_id: uuid.UUID, incidente_id: uuid.UUID
) -> None:
    repo = SqlAlchemyAlertaRepository(db_session)
    creadas = await repo.replace_for_liquidacion(liquidacion_id, [_alerta_generada(incidente_id)])
    creada = creadas[0]

    resultado = await repo.update_estado(
        uuid.uuid4(), creada.id, estado="revisada", justificacion=None
    )

    assert resultado is None
