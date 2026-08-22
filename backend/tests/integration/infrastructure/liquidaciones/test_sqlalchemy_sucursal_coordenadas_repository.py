"""SqlAlchemySucursalCoordenadasRepository contra Postgres real: upsert por
siges_sucursal_id (única), resolución de coordenadas y listado ordenado."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_sucursal_coordenadas_repository import (  # noqa: E501
    SqlAlchemySucursalCoordenadasRepository,
)


def _siges_id() -> int:
    return uuid.uuid4().int % 1_000_000_000


async def test_upsert_pendiente_inserta_y_luego_actualiza_la_misma_fila(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemySucursalCoordenadasRepository(db_session)
    siges_id = _siges_id()
    assert await repo.get_by_siges_sucursal_id(siges_id) is None

    creada = await repo.upsert_pendiente(
        prestador_id=prestador_id,
        siges_sucursal_id=siges_id,
        empresa_nombre="Cencosud",
        sucursal_nombre="Jumbo Palermo",
        direccion_normalizada="av santa fe 4000",
    )
    assert creada.latitud is None
    assert creada.procedencia is None

    otro = await SqlAlchemyPrestadorRepository(db_session).create(
        nombre="Otro", nombre_corto="OTRO", cuit=None, region=None
    )
    actualizada = await repo.upsert_pendiente(
        prestador_id=otro.id,
        siges_sucursal_id=siges_id,
        empresa_nombre="Cencosud",
        sucursal_nombre="Jumbo Palermo II",
        direccion_normalizada=None,
    )
    assert actualizada.id == creada.id
    assert actualizada.prestador_id == otro.id
    assert actualizada.sucursal_nombre == "Jumbo Palermo II"
    assert actualizada.direccion_normalizada is None
    assert await repo.list_by_prestador(prestador_id) == []


async def test_resolver_setea_coordenadas_y_devuelve_none_si_no_existe(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemySucursalCoordenadasRepository(db_session)
    siges_id = _siges_id()
    await repo.upsert_pendiente(
        prestador_id=prestador_id,
        siges_sucursal_id=siges_id,
        empresa_nombre="Cencosud",
        sucursal_nombre="Jumbo",
        direccion_normalizada=None,
    )

    resuelta = await repo.resolver(
        siges_id,
        latitud=-34.58,
        longitud=-58.42,
        procedencia="manual",
        formatted_address="Av. Santa Fe 4000, CABA",
    )
    assert resuelta is not None
    assert (resuelta.latitud, resuelta.longitud) == (-34.58, -58.42)
    assert resuelta.procedencia == "manual"
    assert resuelta.fecha_resolucion is not None

    leida = await repo.get_by_siges_sucursal_id(siges_id)
    assert leida is not None
    assert leida.formatted_address == "Av. Santa Fe 4000, CABA"

    assert (
        await repo.resolver(
            _siges_id(), latitud=0.0, longitud=0.0, procedencia="manual", formatted_address=None
        )
        is None
    )


async def test_list_by_prestador_ordena_por_empresa_y_sucursal(
    db_session: AsyncSession, prestador_id: uuid.UUID
) -> None:
    repo = SqlAlchemySucursalCoordenadasRepository(db_session)
    for empresa, sucursal in (("Zeta", "A"), ("Alfa", "B"), ("Alfa", "A")):
        await repo.upsert_pendiente(
            prestador_id=prestador_id,
            siges_sucursal_id=_siges_id(),
            empresa_nombre=empresa,
            sucursal_nombre=sucursal,
            direccion_normalizada=None,
        )

    listado = await repo.list_by_prestador(prestador_id)

    assert [(s.empresa_nombre, s.sucursal_nombre) for s in listado] == [
        ("Alfa", "A"),
        ("Alfa", "B"),
        ("Zeta", "A"),
    ]
