"""Tests de integración de SqlAlchemyIncidenteRepository contra Postgres real.

Los tests de `update_cobrados`/`delete_by_ids` contra alertas reales son el
corazón de la validación del diseño de reconciliación (ver plan de
reconciliación de liquidaciones, 2026-08-18): confirman contra Postgres de
verdad, no contra un fake, que el UPDATE in-place preserva el triage de la TL
(no cascadea) y que el DELETE sí cascadea (`alertas.incidente_id ON DELETE
CASCADE`) sin levantar un `IntegrityError`."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.services.conciliar_alertas import AlertaConciliada
from src.modules.liquidaciones.domain.value_objects.incidente_actualizado import (
    IncidenteActualizado,
)
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    AlertaGenerada,
    IncidenteEvaluado,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_incidente_repository import (  # noqa: E501
    SqlAlchemyIncidenteRepository,
)

from .conftest import incidente_importado


async def _crear_alerta_descartada(
    db_session: AsyncSession, liquidacion_id: uuid.UUID, incidente_id: uuid.UUID
) -> uuid.UUID:
    """Alerta con triage ya hecho por la TL — la que no puede perderse en un
    `update_cobrados` ni sobrevivir a un `delete_by_ids`."""
    generada = AlertaGenerada(
        incidente_id=incidente_id,
        tipo_alerta="ALT001",
        descripcion="desc",
        riesgo=1.0,
        datos_contexto={},
    )
    conciliada = AlertaConciliada(generada=generada, estado="descartada", justificacion="ok")
    creadas = await SqlAlchemyAlertaRepository(db_session).replace_for_liquidacion(
        liquidacion_id, [conciliada]
    )
    return creadas[0].id


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


def _actualizado(incidente_id: uuid.UUID, **overrides: object) -> IncidenteActualizado:
    base: dict[str, object] = dict(
        incidente_id=incidente_id,
        rubro="Rubro Nuevo",
        tipo="preventivo",
        empresa_nombre="Empresa Nueva",
        sucursal_nombre="Sucursal Nueva",
        nro_serie="SN-2",
        fecha_cierre=None,
        costo_servicio_cobrado=500.0,
        cant_km_cobrado=20.0,
        costo_km_cobrado=6.0,
        total_viaje_cobrado=120.0,
        costo_total_cobrado=620.0,
        pasa_it=False,
    )
    base.update(overrides)
    return IncidenteActualizado(**base)  # type: ignore[arg-type]


async def test_update_cobrados_updates_in_place_preserving_id(
    db_session: AsyncSession, incidente_id: uuid.UUID, liquidacion_id: uuid.UUID
) -> None:
    repo = SqlAlchemyIncidenteRepository(db_session)

    await repo.update_cobrados([_actualizado(incidente_id)])

    fetched = (await repo.list_by_liquidacion(liquidacion_id))[0]
    assert fetched.id == incidente_id
    assert fetched.costo_servicio_cobrado == 500.0
    assert fetched.empresa_nombre == "Empresa Nueva"


async def test_update_cobrados_does_not_cascade_alertas(
    db_session: AsyncSession, incidente_id: uuid.UUID, liquidacion_id: uuid.UUID
) -> None:
    """El corazón del diseño: un UPDATE in-place tiene que dejar intacto el triage
    de la TL — misma alerta, mismo estado, misma justificación."""
    alerta_id = await _crear_alerta_descartada(db_session, liquidacion_id, incidente_id)

    await SqlAlchemyIncidenteRepository(db_session).update_cobrados([_actualizado(incidente_id)])

    alertas = await SqlAlchemyAlertaRepository(db_session).list_by_liquidacion(liquidacion_id)
    assert [a.id for a in alertas] == [alerta_id]
    assert alertas[0].estado == "descartada"
    assert alertas[0].justificacion == "ok"


async def test_delete_by_ids_removes_incidentes(
    db_session: AsyncSession, incidente_id: uuid.UUID, liquidacion_id: uuid.UUID
) -> None:
    eliminados = await SqlAlchemyIncidenteRepository(db_session).delete_by_ids([incidente_id])

    assert eliminados == 1
    assert await SqlAlchemyIncidenteRepository(db_session).list_by_liquidacion(liquidacion_id) == []


async def test_delete_by_ids_with_empty_sequence_returns_zero(db_session: AsyncSession) -> None:
    assert await SqlAlchemyIncidenteRepository(db_session).delete_by_ids([]) == 0


async def test_delete_by_ids_cascades_alertas_without_integrity_error(
    db_session: AsyncSession, incidente_id: uuid.UUID, liquidacion_id: uuid.UUID
) -> None:
    """El otro lado del diseño: borrar un incidente que AyC dejó de reportar no
    puede levantar un IntegrityError por la FK de `alertas.incidente_id` — tiene
    que cascadear (`ON DELETE CASCADE`), y la alerta desaparece con él."""
    await _crear_alerta_descartada(db_session, liquidacion_id, incidente_id)

    eliminados = await SqlAlchemyIncidenteRepository(db_session).delete_by_ids([incidente_id])

    assert eliminados == 1
    alertas = await SqlAlchemyAlertaRepository(db_session).list_by_liquidacion(liquidacion_id)
    assert alertas == []
