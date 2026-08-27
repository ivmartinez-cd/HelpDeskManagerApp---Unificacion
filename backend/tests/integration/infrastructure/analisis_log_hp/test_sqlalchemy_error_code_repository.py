"""Catálogo de códigos de error contra Postgres de test: upsert con semántica
COALESCE/NULLIF (vacío nunca pisa), lookups, paginación y bulk de URLs de ayuda."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analisis_log_hp.infrastructure.repositories.sqlalchemy_error_code_repository import (  # noqa: E501
    SqlAlchemyErrorCodeRepository,
)


async def test_upsert_crea_y_get_by_code_lo_devuelve(db_session: AsyncSession) -> None:
    repo = SqlAlchemyErrorCodeRepository(db_session)
    assert await repo.get_by_code("13.20") is None

    creado = await repo.upsert(
        "13.20", severity="ERROR", description="Atasco", solution_url="http://u",
        solution_content="<p>c</p>",
    )
    leido = await repo.get_by_code("13.20")

    assert leido is not None
    assert (leido.code, leido.severity, leido.description) == ("13.20", "ERROR", "Atasco")
    assert (leido.solution_url, leido.solution_content) == ("http://u", "<p>c</p>")
    assert leido.created_at == creado.created_at


async def test_upsert_con_campos_vacios_no_pisa_los_existentes(db_session: AsyncSession) -> None:
    repo = SqlAlchemyErrorCodeRepository(db_session)
    await repo.upsert("13.20", severity="ERROR", description="Atasco", solution_url="http://u")

    actualizado = await repo.upsert("13.20", severity="", description=None, solution_url="http://v")

    assert (actualizado.severity, actualizado.description) == ("ERROR", "Atasco")
    assert actualizado.solution_url == "http://v"
    assert actualizado.updated_at >= actualizado.created_at


async def test_get_by_codes_devuelve_solo_los_existentes(db_session: AsyncSession) -> None:
    repo = SqlAlchemyErrorCodeRepository(db_session)
    await repo.upsert("A", severity="ERROR")
    await repo.upsert("B", severity="INFO")

    catalogo = await repo.get_by_codes(["A", "B", "Z"])

    assert set(catalogo) == {"A", "B"}
    assert catalogo["B"].severity == "INFO"
    assert await repo.get_by_codes([]) == {}


async def test_list_page_ordena_por_codigo_y_pagina(db_session: AsyncSession) -> None:
    repo = SqlAlchemyErrorCodeRepository(db_session)
    for code in ("C", "A", "B"):
        await repo.upsert(code, severity="INFO")

    items, total = await repo.list_page(page=2, size=2)

    assert total == 3
    assert [c.code for c in items] == ["C"]


async def test_bulk_update_solution_urls_crea_y_actualiza_sin_pisar_con_vacio(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyErrorCodeRepository(db_session)
    await repo.upsert("A", description="Desc original", solution_url="http://a")

    count = await repo.bulk_update_solution_urls({
        "A": {"url": "http://a2", "description": ""},
        "N": {"url": "http://n", "description": "Nuevo"},
        "V": {"url": "", "description": None},
    })

    assert count == 2
    a = await repo.get_by_code("A")
    n = await repo.get_by_code("N")
    assert a is not None and (a.solution_url, a.description) == ("http://a2", "Desc original")
    assert n is not None and (n.solution_url, n.description) == ("http://n", "Nuevo")
    assert await repo.get_by_code("V") is None


async def test_bulk_update_sin_datos_utiles_no_escribe(db_session: AsyncSession) -> None:
    repo = SqlAlchemyErrorCodeRepository(db_session)
    assert await repo.bulk_update_solution_urls({"X": {"url": None}}) == 0
    assert await repo.get_by_code("X") is None
