"""Tests de integración de SqlAlchemyTarifarioZonaMapRepository contra Postgres real."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_zona_map_repository import (  # noqa: E501
    SqlAlchemyTarifarioZonaMapRepository,
)


async def _create_spst(db_session: AsyncSession, prestador_id: uuid.UUID, nombre: str):
    return await SqlAlchemySpstRepository(db_session).create(
        prestador_id=prestador_id,
        nombre=nombre,
        domicilio=None,
        localidad=None,
        provincia=None,
        zona_cobertura=None,
    )


async def test_upsert_crea_y_luego_pisa(db_session: AsyncSession, prestador_id: uuid.UUID) -> None:
    repo = SqlAlchemyTarifarioZonaMapRepository(db_session)
    ushuaia = await _create_spst(db_session, prestador_id, "Ushuaia")
    ushuaia_y_alrededores = await _create_spst(db_session, prestador_id, "Ushuaia y alrededores")

    creado = await repo.upsert(
        prestador_id=prestador_id,
        descripcion_siges="Ushuaia - Infomac",
        spst_id=ushuaia.id,
    )
    assert creado.spst_id == ushuaia.id

    pisado = await repo.upsert(
        prestador_id=prestador_id,
        descripcion_siges="Ushuaia - Infomac",
        spst_id=ushuaia_y_alrededores.id,
    )
    assert pisado.id == creado.id  # misma fila, no duplica
    assert pisado.spst_id == ushuaia_y_alrededores.id

    todos = await repo.list_all()
    propios = [m for m in todos if m.prestador_id == prestador_id]
    assert len(propios) == 1


async def test_list_all_ordena_por_prestador_y_descripcion(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyTarifarioZonaMapRepository(db_session)
    await repo.upsert(prestador_id=prestador_id, descripcion_siges="B zona", spst_id=None)
    await repo.upsert(prestador_id=prestador_id, descripcion_siges="A zona", spst_id=None)

    propios = [m for m in await repo.list_all() if m.prestador_id == prestador_id]

    assert [m.descripcion_siges for m in propios] == ["A zona", "B zona"]
