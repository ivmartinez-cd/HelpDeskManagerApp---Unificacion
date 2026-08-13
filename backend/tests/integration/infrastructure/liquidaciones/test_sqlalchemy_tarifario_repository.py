"""Tests de integración de SqlAlchemyTarifarioRepository contra Postgres real."""

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_repository import (  # noqa: E501
    SqlAlchemyTarifarioRepository,
)


async def _create_tarifario(
    db_session: AsyncSession,
    prestador_id: uuid.UUID,
    *,
    tipo_servicio: str = "correctivo",
    zona: str | None = "AMBA",
    vigencia_desde: date = date(2026, 1, 1),
    vigencia_hasta: date | None = None,
):
    return await SqlAlchemyTarifarioRepository(db_session).create(
        prestador_id=prestador_id,
        tipo_servicio=tipo_servicio,
        zona=zona,
        costo_servicio=1000.0,
        costo_km=50.0,
        vigencia_desde=vigencia_desde,
        vigencia_hasta=vigencia_hasta,
    )


async def test_create_then_get_by_id_round_trips(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    created = await _create_tarifario(db_session, prestador_id)

    fetched = await SqlAlchemyTarifarioRepository(db_session).get_by_id(created.id)
    assert fetched is not None
    assert fetched.costo_servicio == 1000.0


async def test_list_by_prestador_only_returns_own_tarifarios(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    otro_prestador = await SqlAlchemyPrestadorRepository(db_session).create(
        nombre="Otro", nombre_corto="OTRO", cuit=None, region=None
    )
    propio = await _create_tarifario(db_session, prestador_id)
    await _create_tarifario(db_session, otro_prestador.id)

    resultado = await SqlAlchemyTarifarioRepository(db_session).list_by_prestador(prestador_id)

    assert [t.id for t in resultado] == [propio.id]


async def test_list_grupo_matches_tipo_servicio_y_zona_exacta(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyTarifarioRepository(db_session)
    del_grupo = await _create_tarifario(db_session, prestador_id, zona="AMBA")
    await _create_tarifario(db_session, prestador_id, zona="Interior")
    await _create_tarifario(db_session, prestador_id, zona=None)

    resultado = await repo.list_grupo(
        prestador_id=prestador_id, tipo_servicio="correctivo", zona="AMBA"
    )

    assert [t.id for t in resultado] == [del_grupo.id]


async def test_list_grupo_con_zona_none_matches_solo_zona_none(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyTarifarioRepository(db_session)
    await _create_tarifario(db_session, prestador_id, zona="AMBA")
    sin_zona = await _create_tarifario(db_session, prestador_id, zona=None)

    resultado = await repo.list_grupo(
        prestador_id=prestador_id, tipo_servicio="correctivo", zona=None
    )

    assert [t.id for t in resultado] == [sin_zona.id]


async def test_set_vigencia_hasta_updates_only_that_field(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyTarifarioRepository(db_session)
    created = await _create_tarifario(db_session, prestador_id)

    await repo.set_vigencia_hasta(created.id, date(2026, 6, 30))

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.vigencia_hasta == date(2026, 6, 30)


async def test_set_vigencia_hasta_is_noop_when_missing(db_session: AsyncSession) -> None:
    await SqlAlchemyTarifarioRepository(db_session).set_vigencia_hasta(
        uuid.uuid4(), date(2026, 1, 1)
    )  # no debe lanzar


async def test_delete_removes_tarifario(db_session: AsyncSession, prestador_id: uuid.UUID) -> None:
    repo = SqlAlchemyTarifarioRepository(db_session)
    created = await _create_tarifario(db_session, prestador_id)

    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id) is None


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    assert await SqlAlchemyTarifarioRepository(db_session).delete(uuid.uuid4()) is False
