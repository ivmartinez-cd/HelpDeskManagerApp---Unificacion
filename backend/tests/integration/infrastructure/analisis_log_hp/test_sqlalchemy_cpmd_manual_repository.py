"""Catálogo de manuales CPMD contra Postgres de test: alta con ARRAY de keywords,
lookup por id y matching substring case-insensitive por familia de modelo."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.infrastructure.repositories.sqlalchemy_cpmd_manual_repository import (  # noqa: E501
    SqlAlchemyCpmdManualRepository,
)


async def test_create_y_get_by_id_round_trip(db_session: AsyncSession) -> None:
    repo = SqlAlchemyCpmdManualRepository(db_session)

    creado = await repo.create(keywords=["M404", "M428"], label="LaserJet M4xx", filename="a.pdf")
    leido = await repo.get_by_id(creado.id)

    assert leido is not None
    assert leido.keywords == ["M404", "M428"]
    assert (leido.label, leido.filename) == ("LaserJet M4xx", "a.pdf")
    assert leido.uploaded_at.tzinfo is not None
    assert await repo.get_by_id(creado.id + 1000) is None


async def test_find_by_model_family_matchea_keyword_case_insensitive(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyCpmdManualRepository(db_session)
    await repo.create(keywords=["E52645"], label="Enterprise", filename="e.pdf")
    m4 = await repo.create(keywords=["M404", "m428"], label="M4xx", filename="m.pdf")

    encontrado = await repo.find_by_model_family("HP LaserJet Pro m428fdw")

    assert encontrado is not None and encontrado.id == m4.id
    assert await repo.find_by_model_family("Brother HL-1200") is None
