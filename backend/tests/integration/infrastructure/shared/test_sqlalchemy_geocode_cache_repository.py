"""Cache de geocodes por dirección normalizada (upsert del payload) contra
Postgres real — compartido entre liquidaciones y preventivos."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato
from src.shared.infrastructure.geocoding.sqlalchemy_geocode_cache_repository import (  # noqa: E501
    SqlAlchemyGeocodeCacheRepository,
)


async def test_geocode_cache_put_inserta_y_luego_reemplaza(db_session: AsyncSession) -> None:
    repo = SqlAlchemyGeocodeCacheRepository(db_session)
    direccion = f"av siempre viva 742 {uuid.uuid4().hex[:8]}"
    assert await repo.get(direccion) is None

    candidato = GeocodeCandidato(
        formatted_address="Av. Siempre Viva 742, Springfield",
        latitud=-31.5,
        longitud=-68.5,
        location_type="ROOFTOP",
        tipos=("street_address",),
        partial_match=True,
    )
    await repo.put(direccion, [candidato])
    assert await repo.get(direccion) == [candidato]

    # ZERO_RESULTS también se cachea (lista vacía) y pisa el payload anterior.
    await repo.put(direccion, [])
    assert await repo.get(direccion) == []
