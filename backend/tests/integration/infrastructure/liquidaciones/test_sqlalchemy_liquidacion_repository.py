"""Tests de integración de SqlAlchemyLiquidacionRepository contra Postgres real."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)


async def _create_liquidacion(
    db_session: AsyncSession,
    prestador_id: uuid.UUID,
    *,
    numero_liquidacion: str = "1-1",
    nombre_archivo: str | None = None,
    total_incidentes: int = 0,
    total_importe: float = 0.0,
):
    return await SqlAlchemyLiquidacionRepository(db_session).create(
        prestador_id=prestador_id,
        numero_liquidacion=numero_liquidacion,
        periodo="2026-01",
        tipo_liquidacion="regular",
        nombre_archivo=nombre_archivo,
        total_incidentes=total_incidentes,
        total_importe=total_importe,
    )


async def test_create_then_get_by_id_round_trips(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    created = await _create_liquidacion(
        db_session,
        prestador_id,
        numero_liquidacion="3739-6",
        nombre_archivo="liquidacion_3739-6.xls",
        total_incidentes=107,
        total_importe=12345.67,
    )

    fetched = await SqlAlchemyLiquidacionRepository(db_session).get_by_id(created.id)
    assert fetched is not None
    assert fetched.numero_liquidacion == "3739-6"
    assert fetched.estado == "abierta"  # default de la columna


async def test_list_by_prestador_only_returns_own_liquidaciones(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    otro_prestador = await SqlAlchemyPrestadorRepository(db_session).create(
        nombre="Otro", nombre_corto="OTRO", cuit=None, region=None
    )
    propia = await _create_liquidacion(db_session, prestador_id)
    await _create_liquidacion(db_session, otro_prestador.id)

    resultado = await SqlAlchemyLiquidacionRepository(db_session).list_by_prestador(prestador_id)

    assert [liq.id for liq in resultado] == [propia.id]


async def test_update_estado_changes_estado(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    created = await _create_liquidacion(db_session, prestador_id)

    updated = await SqlAlchemyLiquidacionRepository(db_session).update_estado(
        created.id, "cerrada"
    )

    assert updated is not None
    assert updated.estado == "cerrada"


async def test_update_estado_returns_none_when_missing(db_session: AsyncSession) -> None:
    resultado = await SqlAlchemyLiquidacionRepository(db_session).update_estado(
        uuid.uuid4(), "cerrada"
    )
    assert resultado is None


async def test_update_total_alertas_persists_count(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyLiquidacionRepository(db_session)
    created = await _create_liquidacion(db_session, prestador_id)

    await repo.update_total_alertas(created.id, 5)

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.total_alertas == 5


async def test_delete_removes_liquidacion(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyLiquidacionRepository(db_session)
    created = await _create_liquidacion(db_session, prestador_id)

    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id) is None


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    assert await SqlAlchemyLiquidacionRepository(db_session).delete(uuid.uuid4()) is False


async def test_list_filtered_by_estado(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyLiquidacionRepository(db_session)
    abierta = await _create_liquidacion(db_session, prestador_id)
    await repo.update_estado(abierta.id, "aprobada")

    resultado = await repo.list_filtered(estado="aprobada")

    ids = [liq.id for liq in resultado]
    assert abierta.id in ids


async def test_list_filtered_by_periodo(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyLiquidacionRepository(db_session)
    await repo.create(
        prestador_id=prestador_id,
        numero_liquidacion="1-1",
        periodo="2025-12",
        tipo_liquidacion="regular",
        nombre_archivo=None,
        total_incidentes=0,
        total_importe=0.0,
    )
    await repo.create(
        prestador_id=prestador_id,
        numero_liquidacion="1-2",
        periodo="2026-01",
        tipo_liquidacion="regular",
        nombre_archivo=None,
        total_incidentes=0,
        total_importe=0.0,
    )

    resultado = await repo.list_filtered(periodo="2025-12")

    assert all(liq.periodo == "2025-12" for liq in resultado)
    assert len(resultado) >= 1


async def test_list_periodos_returns_distinct_sorted(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyLiquidacionRepository(db_session)
    for periodo in ["2026-01", "2026-02", "2026-01"]:
        await repo.create(
            prestador_id=prestador_id,
            numero_liquidacion=None,
            periodo=periodo,
            tipo_liquidacion="regular",
            nombre_archivo=None,
            total_incidentes=0,
            total_importe=0.0,
        )

    periodos = await repo.list_periodos()

    assert "2026-01" in periodos
    assert "2026-02" in periodos
    assert periodos.count("2026-01") == 1
    assert periodos.index("2026-02") < periodos.index("2026-01")
