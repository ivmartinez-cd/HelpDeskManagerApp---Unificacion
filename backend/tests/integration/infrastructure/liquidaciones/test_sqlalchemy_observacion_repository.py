"""Tests de integración de SqlAlchemyObservacionRepository contra Postgres real."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    ObservacionGenerada,
)
from src.modules.liquidaciones.infrastructure.models.observacion_model import (
    ObservacionIncidenteModel,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_incidente_repository import (  # noqa: E501
    SqlAlchemyIncidenteRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_observacion_repository import (  # noqa: E501
    SqlAlchemyObservacionRepository,
)

from .conftest import incidente_importado


async def _dos_incidentes(
    db_session: AsyncSession, liquidacion_id: uuid.UUID
) -> tuple[uuid.UUID, uuid.UUID]:
    creados = await SqlAlchemyIncidenteRepository(db_session).bulk_create(
        liquidacion_id,
        [
            incidente_importado(numero_incidente="INC-A"),
            incidente_importado(numero_incidente="INC-B"),
        ],
    )
    return creados[0].id, creados[1].id


def _observacion_generada(principal: uuid.UUID, referencia: uuid.UUID) -> ObservacionGenerada:
    return ObservacionGenerada(
        tipo_observacion="ruta_compartida",
        severidad="media",
        titulo="Ruta compartida",
        descripcion="Dos incidentes en la misma localidad",
        monto_cobrado=100.0,
        monto_esperado=80.0,
        incidentes_relacionados=[principal, referencia],
        incidente_principal_id=principal,
        regla_codigo="ALT005",
        datos_contexto={"corredor": "AMBA"},
    )


async def test_replace_for_liquidacion_creates_observacion_con_vinculos(
    db_session: AsyncSession, liquidacion_id: uuid.UUID
) -> None:
    principal, referencia = await _dos_incidentes(db_session, liquidacion_id)
    repo = SqlAlchemyObservacionRepository(db_session)

    creadas = await repo.replace_for_liquidacion(
        liquidacion_id, [_observacion_generada(principal, referencia)]
    )

    assert len(creadas) == 1
    assert creadas[0].diferencia == 20.0
    vinculos = (
        await db_session.execute(
            select(ObservacionIncidenteModel).where(
                ObservacionIncidenteModel.observacion_id == creadas[0].id
            )
        )
    ).scalars().all()
    assert {v.incidente_id for v in vinculos} == {principal, referencia}
    roles = {v.incidente_id: v.rol for v in vinculos}
    assert roles[principal] == "principal"
    assert roles[referencia] == "referencia"


async def test_replace_for_liquidacion_discards_previous_observaciones(
    db_session: AsyncSession, liquidacion_id: uuid.UUID
) -> None:
    principal, referencia = await _dos_incidentes(db_session, liquidacion_id)
    repo = SqlAlchemyObservacionRepository(db_session)
    await repo.replace_for_liquidacion(
        liquidacion_id, [_observacion_generada(principal, referencia)]
    )

    segunda_pasada = await repo.replace_for_liquidacion(liquidacion_id, [])

    assert segunda_pasada == []
    assert await repo.list_by_liquidacion(liquidacion_id) == []


async def test_update_estado_changes_estado(
    db_session: AsyncSession, liquidacion_id: uuid.UUID
) -> None:
    principal, referencia = await _dos_incidentes(db_session, liquidacion_id)
    repo = SqlAlchemyObservacionRepository(db_session)
    creada = (
        await repo.replace_for_liquidacion(
            liquidacion_id, [_observacion_generada(principal, referencia)]
        )
    )[0]

    actualizada = await repo.update_estado(liquidacion_id, creada.id, "revisada")

    assert actualizada is not None
    assert actualizada.estado == "revisada"


async def test_update_estado_returns_none_when_liquidacion_no_coincide(
    db_session: AsyncSession, liquidacion_id: uuid.UUID
) -> None:
    principal, referencia = await _dos_incidentes(db_session, liquidacion_id)
    repo = SqlAlchemyObservacionRepository(db_session)
    creada = (
        await repo.replace_for_liquidacion(
            liquidacion_id, [_observacion_generada(principal, referencia)]
        )
    )[0]

    resultado = await repo.update_estado(uuid.uuid4(), creada.id, "revisada")

    assert resultado is None
