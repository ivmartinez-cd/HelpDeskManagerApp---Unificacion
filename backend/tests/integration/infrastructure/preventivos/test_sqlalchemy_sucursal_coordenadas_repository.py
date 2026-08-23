"""SqlAlchemySucursalCoordenadasRepository contra Postgres real: upsert por
siges_sucursal_id (única) y listado filtrado por ids."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.preventivos.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.preventivos.infrastructure.repositories.sqlalchemy_sucursal_coordenadas_repository import (  # noqa: E501
    SqlAlchemySucursalCoordenadasRepository,
)


def _siges_id() -> int:
    return uuid.uuid4().int % 1_000_000_000


async def test_upsert_inserta_y_luego_actualiza_la_misma_fila(db_session: AsyncSession) -> None:
    repo = SqlAlchemySucursalCoordenadasRepository(db_session)
    siges_id = _siges_id()
    assert await repo.list_by_siges_sucursal_ids([siges_id]) == {}

    await repo.upsert(
        SucursalCoordenadas(
            siges_sucursal_id=siges_id,
            latitud=-31.5,
            longitud=-68.5,
            formatted_address="Domicilio original",
            fecha_resolucion=datetime.now(UTC),
        )
    )
    resultado = await repo.list_by_siges_sucursal_ids([siges_id])
    assert resultado[siges_id].formatted_address == "Domicilio original"

    await repo.upsert(
        SucursalCoordenadas(
            siges_sucursal_id=siges_id,
            latitud=-31.6,
            longitud=-68.6,
            formatted_address="Domicilio corregido",
            fecha_resolucion=datetime.now(UTC),
        )
    )
    actualizado = await repo.list_by_siges_sucursal_ids([siges_id])
    assert len(actualizado) == 1
    assert actualizado[siges_id].formatted_address == "Domicilio corregido"
    assert actualizado[siges_id].latitud == -31.6


async def test_list_by_siges_sucursal_ids_filtra_y_omite_no_resueltas(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemySucursalCoordenadasRepository(db_session)
    resuelta_id, otra_id, sin_resolver_id = _siges_id(), _siges_id(), _siges_id()
    await repo.upsert(
        SucursalCoordenadas(resuelta_id, -31.5, -68.5, "Resuelta", datetime.now(UTC))
    )
    await repo.upsert(SucursalCoordenadas(otra_id, -31.4, -68.4, "Otra", datetime.now(UTC)))

    resultado = await repo.list_by_siges_sucursal_ids([resuelta_id, sin_resolver_id])

    assert set(resultado) == {resuelta_id}
    assert otra_id not in resultado
