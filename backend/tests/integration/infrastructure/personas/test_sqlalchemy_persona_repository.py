"""Lectura unificada ficha + cuenta contra Postgres (ADR-040)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.personas.domain.repositories.persona_repository import (
    FiltrosPersonas,
    OrdenPersonas,
)
from src.modules.personas.infrastructure.sqlalchemy_persona_repository import (
    SqlAlchemyPersonaRepository,
)
from src.modules.vacaciones.domain.entities.empleado import EstadoEmpleado
from tests.integration.infrastructure.personas.conftest import alta_empleado, crear_usuario


async def test_get_trae_ficha_sector_cargo_y_acceso(
    db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    user_id = await crear_usuario(db_session)
    empleado = await alta_empleado(db_session, sector_id, cargo_id, user_id=user_id)

    persona = await SqlAlchemyPersonaRepository(db_session).get(empleado.id)

    assert persona is not None
    assert persona.datos.email == empleado.email
    assert persona.sector_id == sector_id and persona.sector_nombre.startswith("Sector ")
    assert persona.cargo_nombre.startswith("Cargo ")
    assert persona.acceso is not None and persona.acceso.user_id == user_id
    assert persona.entra_a_la_app


async def test_cuenta_placeholder_no_cuenta_como_acceso(
    db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    user_id = await crear_usuario(db_session, placeholder=True)
    empleado = await alta_empleado(db_session, sector_id, cargo_id, user_id=user_id)

    persona = await SqlAlchemyPersonaRepository(db_session).get(empleado.id)

    assert persona is not None and persona.acceso is None


async def test_get_de_ficha_inexistente_es_none(db_session: AsyncSession) -> None:
    assert await SqlAlchemyPersonaRepository(db_session).get(uuid.uuid4()) is None


async def test_list_page_filtra_y_pagina(
    db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    con_cuenta = await alta_empleado(
        db_session, sector_id, cargo_id, first_name="Zoe", user_id=await crear_usuario(db_session)
    )
    await alta_empleado(db_session, sector_id, cargo_id, first_name="Ana")
    await alta_empleado(
        db_session, sector_id, cargo_id, first_name="Beto", status=EstadoEmpleado.INACTIVE
    )
    repo = SqlAlchemyPersonaRepository(db_session)
    del_sector = FiltrosPersonas(sector_id=sector_id)

    todas, total = await repo.list_page(del_sector, OrdenPersonas(), page=1, size=10)
    pagina, _ = await repo.list_page(del_sector, OrdenPersonas(), page=2, size=2)
    activas, _ = await repo.list_page(
        FiltrosPersonas(sector_id=sector_id, activa=True), OrdenPersonas(), page=1, size=10
    )
    entran, _ = await repo.list_page(
        FiltrosPersonas(sector_id=sector_id, entra_a_la_app=True), OrdenPersonas(), page=1, size=10
    )
    buscada, _ = await repo.list_page(
        FiltrosPersonas(busqueda="zoe", sector_id=sector_id), OrdenPersonas(), page=1, size=10
    )

    assert total == 3
    assert [p.datos.first_name for p in todas] == ["Ana", "Beto", "Zoe"]
    assert [p.datos.first_name for p in pagina] == ["Zoe"]
    assert {p.datos.first_name for p in activas} == {"Ana", "Zoe"}
    assert [p.id for p in entran] == [con_cuenta.id]
    assert [p.id for p in buscada] == [con_cuenta.id]


async def test_orden_por_acceso_pone_primero_a_quien_entra(
    db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    await alta_empleado(db_session, sector_id, cargo_id, first_name="Ana")
    con_cuenta = await alta_empleado(
        db_session, sector_id, cargo_id, first_name="Zoe", user_id=await crear_usuario(db_session)
    )
    repo = SqlAlchemyPersonaRepository(db_session)

    asc, _ = await repo.list_page(
        FiltrosPersonas(sector_id=sector_id), OrdenPersonas("acceso"), page=1, size=10
    )
    desc, _ = await repo.list_page(
        FiltrosPersonas(sector_id=sector_id), OrdenPersonas("acceso", True), page=1, size=10
    )

    assert asc[0].id == con_cuenta.id
    assert desc[-1].id == con_cuenta.id
