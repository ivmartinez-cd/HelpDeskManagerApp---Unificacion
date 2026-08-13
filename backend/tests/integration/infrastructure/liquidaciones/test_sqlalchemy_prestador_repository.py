"""Tests de integración de SqlAlchemyPrestadorRepository contra Postgres real."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.errors import (
    PrestadorConLiquidacionesError,
    SigesVinculoDuplicadoError,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)


async def test_create_then_get_by_id_round_trips(db_session: AsyncSession) -> None:
    repo = SqlAlchemyPrestadorRepository(db_session)

    created = await repo.create(
        nombre="Pentacom", nombre_corto="PENTACOM", cuit="20-1-1", region="AMBA"
    )

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.nombre_corto == "PENTACOM"
    assert fetched.activo is True


async def test_get_by_nombre_corto_returns_none_when_missing(db_session: AsyncSession) -> None:
    repo = SqlAlchemyPrestadorRepository(db_session)

    assert await repo.get_by_nombre_corto("NO-EXISTE") is None


async def test_list_all_solo_activos_filters_inactive(db_session: AsyncSession) -> None:
    repo = SqlAlchemyPrestadorRepository(db_session)
    activo = await repo.create(nombre="Activo", nombre_corto="ACT", cuit=None, region=None)
    inactivo = await repo.create(nombre="Inactivo", nombre_corto="INACT", cuit=None, region=None)
    await repo.toggle_activo(inactivo.id, activo=False)

    solo_activos = await repo.list_all(solo_activos=True)

    ids = {p.id for p in solo_activos}
    assert activo.id in ids
    assert inactivo.id not in ids


async def test_update_changes_fields(db_session: AsyncSession) -> None:
    repo = SqlAlchemyPrestadorRepository(db_session)
    created = await repo.create(nombre="Viejo", nombre_corto="VIEJO", cuit=None, region=None)

    updated = await repo.update(
        created.id, nombre="Nuevo", nombre_corto="NUEVO", cuit="30-2-2", region="Cordoba"
    )

    assert updated is not None
    assert updated.nombre == "Nuevo"
    assert updated.cuit == "30-2-2"


async def test_delete_removes_prestador_without_relacionados(db_session: AsyncSession) -> None:
    repo = SqlAlchemyPrestadorRepository(db_session)
    created = await repo.create(nombre="Descartable", nombre_corto="DESC", cuit=None, region=None)

    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id) is None


async def test_delete_returns_false_when_missing(db_session: AsyncSession) -> None:
    repo = SqlAlchemyPrestadorRepository(db_session)

    assert await repo.delete(uuid.uuid4()) is False


async def test_delete_raises_when_prestador_has_liquidaciones(db_session: AsyncSession) -> None:
    prestador_repo = SqlAlchemyPrestadorRepository(db_session)
    liquidacion_repo = SqlAlchemyLiquidacionRepository(db_session)
    prestador = await prestador_repo.create(
        nombre="Con Historial", nombre_corto="CONHIST", cuit=None, region=None
    )
    await liquidacion_repo.create(
        prestador_id=prestador.id,
        numero_liquidacion="1-1",
        periodo="2026-01",
        tipo_liquidacion="regular",
        nombre_archivo=None,
        total_incidentes=0,
        total_importe=0.0,
    )

    with pytest.raises(PrestadorConLiquidacionesError):
        await prestador_repo.delete(prestador.id)


async def test_vincular_siges_set_y_unset(db_session: AsyncSession) -> None:
    repo = SqlAlchemyPrestadorRepository(db_session)
    created = await repo.create(nombre="Vinculable", nombre_corto="VINC", cuit=None, region=None)

    vinculado = await repo.vincular_siges(created.id, siges_empresa_id=137)
    assert vinculado is not None
    assert vinculado.siges_empresa_id == 137

    desvinculado = await repo.vincular_siges(created.id, siges_empresa_id=None)
    assert desvinculado is not None
    assert desvinculado.siges_empresa_id is None


async def test_vincular_siges_duplicado_lanza_error_de_dominio(db_session: AsyncSession) -> None:
    repo = SqlAlchemyPrestadorRepository(db_session)
    uno = await repo.create(nombre="Uno", nombre_corto="UNO", cuit=None, region=None)
    dos = await repo.create(nombre="Dos", nombre_corto="DOS", cuit=None, region=None)
    await repo.vincular_siges(uno.id, siges_empresa_id=600)

    with pytest.raises(SigesVinculoDuplicadoError):
        await repo.vincular_siges(dos.id, siges_empresa_id=600)
