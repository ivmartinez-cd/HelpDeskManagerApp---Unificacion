"""Tests de integración de SqlAlchemyTablaKmRepository contra Postgres real."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (  # noqa: E501
    SqlAlchemyTablaKmRepository,
)


async def _create_entrada(
    db_session: AsyncSession,
    prestador_id: uuid.UUID,
    *,
    empresa_nombre: str = "Empresa A",
    sucursal_nombre: str = "Sucursal 1",
):
    return await SqlAlchemyTablaKmRepository(db_session).create(
        prestador_id=prestador_id,
        spst_id=None,
        empresa_nombre=empresa_nombre,
        sucursal_nombre=sucursal_nombre,
        observaciones=None,
        domicilio_cliente=None,
        localidad_cliente=None,
        provincia_cliente=None,
        kms_recorrido=20.0,
        umbral_viatico=10.0,
        aplica_viatico=True,
        kms_a_facturar=20.0,
        url_maps=None,
    )


async def test_create_then_get_by_id_round_trips(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    created = await _create_entrada(db_session, prestador_id)

    fetched = await SqlAlchemyTablaKmRepository(db_session).get_by_id(created.id)
    assert fetched is not None
    assert fetched.empresa_nombre == "Empresa A"


async def test_list_by_prestador_only_returns_own_entradas(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    otro_prestador = await SqlAlchemyPrestadorRepository(db_session).create(
        nombre="Otro", nombre_corto="OTRO", cuit=None, region=None
    )
    propia = await _create_entrada(db_session, prestador_id)
    await _create_entrada(db_session, otro_prestador.id)

    resultado = await SqlAlchemyTablaKmRepository(db_session).list_by_prestador(prestador_id)

    assert [t.id for t in resultado] == [propia.id]


async def test_list_all_filters_by_q_case_insensitive(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemyTablaKmRepository(db_session)
    match = await _create_entrada(db_session, prestador_id, empresa_nombre="Cencosud")
    await _create_entrada(db_session, prestador_id, empresa_nombre="Otra Empresa")

    resultado = await repo.list_all(prestador_id=prestador_id, q="cenco")

    assert [t.id for t in resultado] == [match.id]


async def test_update_changes_fields(db_session: AsyncSession, prestador_id: uuid.UUID) -> None:
    repo = SqlAlchemyTablaKmRepository(db_session)
    created = await _create_entrada(db_session, prestador_id)

    updated = await repo.update(
        created.id,
        prestador_id=prestador_id,
        spst_id=None,
        empresa_nombre="Renombrada",
        sucursal_nombre="Sucursal 2",
        observaciones="obs",
        domicilio_cliente=None,
        localidad_cliente=None,
        provincia_cliente=None,
        kms_recorrido=30.0,
        umbral_viatico=15.0,
        aplica_viatico=False,
        kms_a_facturar=30.0,
        url_maps=None,
    )

    assert updated is not None
    assert updated.empresa_nombre == "Renombrada"
    assert updated.kms_recorrido == 30.0


async def test_delete_removes_entrada(db_session: AsyncSession, prestador_id: uuid.UUID) -> None:
    repo = SqlAlchemyTablaKmRepository(db_session)
    created = await _create_entrada(db_session, prestador_id)

    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id) is None


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    assert await SqlAlchemyTablaKmRepository(db_session).delete(uuid.uuid4()) is False
