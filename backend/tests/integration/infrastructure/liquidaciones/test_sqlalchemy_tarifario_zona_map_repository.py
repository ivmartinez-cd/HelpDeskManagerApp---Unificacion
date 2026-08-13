"""Tests de integración de SqlAlchemyTarifarioZonaMapRepository contra Postgres real."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tarifario_zona_map_repository import (  # noqa: E501
    SqlAlchemyTarifarioZonaMapRepository,
)


async def test_upsert_crea_y_luego_pisa(db_session: AsyncSession, prestador_id: uuid.UUID) -> None:
    repo = SqlAlchemyTarifarioZonaMapRepository(db_session)

    creado = await repo.upsert(
        prestador_id=prestador_id,
        descripcion_siges="Ushuaia - Infomac",
        zona_local="Ushuaia",
    )
    assert creado.zona_local == "Ushuaia"

    pisado = await repo.upsert(
        prestador_id=prestador_id,
        descripcion_siges="Ushuaia - Infomac",
        zona_local="Ushuaia y alrededores",
    )
    assert pisado.id == creado.id  # misma fila, no duplica
    assert pisado.zona_local == "Ushuaia y alrededores"

    todos = await repo.list_all()
    propios = [m for m in todos if m.prestador_id == prestador_id]
    assert len(propios) == 1


async def test_list_all_ordena_por_prestador_y_descripcion(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyTarifarioZonaMapRepository(db_session)
    await repo.upsert(prestador_id=prestador_id, descripcion_siges="B zona", zona_local="B")
    await repo.upsert(prestador_id=prestador_id, descripcion_siges="A zona", zona_local="A")

    propios = [m for m in await repo.list_all() if m.prestador_id == prestador_id]

    assert [m.descripcion_siges for m in propios] == ["A zona", "B zona"]
