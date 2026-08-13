"""Tests de integración de SqlAlchemySpstRepository contra Postgres real."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_spst_repository import (
    SqlAlchemySpstRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_tabla_km_repository import (  # noqa: E501
    SqlAlchemyTablaKmRepository,
)


async def _create_spst(db_session: AsyncSession, prestador_id: uuid.UUID, nombre: str = "SPST 1"):
    return await SqlAlchemySpstRepository(db_session).create(
        prestador_id=prestador_id,
        nombre=nombre,
        domicilio="Calle 1",
        localidad="CABA",
        provincia="Buenos Aires",
        zona="AMBA",
    )


async def test_create_then_get_by_id_round_trips(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    created = await _create_spst(db_session, prestador_id)

    fetched = await SqlAlchemySpstRepository(db_session).get_by_id(created.id)
    assert fetched is not None
    assert fetched.nombre == "SPST 1"
    assert fetched.prestador_id == prestador_id


async def test_list_by_prestador_only_returns_own_spsts(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    otro_prestador = await SqlAlchemyPrestadorRepository(db_session).create(
        nombre="Otro", nombre_corto="OTRO", cuit=None, region=None
    )
    propio = await _create_spst(db_session, prestador_id, "Propio")
    await _create_spst(db_session, otro_prestador.id, "Ajeno")

    resultado = await SqlAlchemySpstRepository(db_session).list_by_prestador(prestador_id)

    assert [s.id for s in resultado] == [propio.id]


async def test_list_all_filters_by_prestador_and_activos(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemySpstRepository(db_session)
    inactivo = await _create_spst(db_session, prestador_id, "Inactivo")
    await repo.toggle_activo(inactivo.id, activo=False)

    solo_activos = await repo.list_all(prestador_id=prestador_id, solo_activos=True)

    assert inactivo.id not in {s.id for s in solo_activos}


async def test_update_changes_fields(db_session: AsyncSession, prestador_id: uuid.UUID) -> None:
    repo = SqlAlchemySpstRepository(db_session)
    created = await _create_spst(db_session, prestador_id)

    updated = await repo.update(
        created.id,
        nombre="Renombrado",
        domicilio="Calle 2",
        localidad="Cordoba",
        provincia="Cordoba",
        zona="Interior",
    )

    assert updated is not None
    assert updated.nombre == "Renombrado"
    assert updated.zona == "Interior"


async def test_delete_sets_null_on_related_tabla_km_instead_of_blocking(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    spst = await _create_spst(db_session, prestador_id)
    tabla_km_repo = SqlAlchemyTablaKmRepository(db_session)
    entrada = await tabla_km_repo.create(
        prestador_id=prestador_id,
        spst_id=spst.id,
        empresa_nombre="Empresa",
        sucursal_nombre="Sucursal",
        observaciones=None,
        domicilio_cliente=None,
        localidad_cliente=None,
        provincia_cliente=None,
        kms_recorrido=10.0,
        umbral_viatico=5.0,
        aplica_viatico=False,
        kms_a_facturar=10.0,
        url_maps=None,
    )

    assert await SqlAlchemySpstRepository(db_session).delete(spst.id) is True

    tras_delete = await tabla_km_repo.get_by_id(entrada.id)
    assert tras_delete is not None
    assert tras_delete.spst_id is None


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    assert await SqlAlchemySpstRepository(db_session).delete(uuid.uuid4()) is False


async def test_vincular_siges_set_y_unset(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemySpstRepository(db_session)
    created = await _create_spst(db_session, prestador_id)

    vinculado = await repo.vincular_siges(created.id, siges_empresa_id=138)
    assert vinculado is not None
    assert vinculado.siges_empresa_id == 138

    desvinculado = await repo.vincular_siges(created.id, siges_empresa_id=None)
    assert desvinculado is not None
    assert desvinculado.siges_empresa_id is None
