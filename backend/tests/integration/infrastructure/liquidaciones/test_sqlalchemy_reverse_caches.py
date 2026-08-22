"""Caches de geolocalización contra Postgres real: reverse Georef, reverse
Nominatim (clave por coordenadas redondeadas, el "sin cobertura" también se
cachea) y cache de geocodes por dirección normalizada (upsert del payload)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.repositories.geocoding_gateway import GeocodeCandidato
from src.modules.liquidaciones.domain.repositories.georeferenciacion_gateway import (
    UbicacionGeoref,
)
from src.modules.liquidaciones.domain.repositories.nominatim_gateway import (
    UbicacionNominatim,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_geocode_cache_repository import (  # noqa: E501
    SqlAlchemyGeocodeCacheRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_georef_reverse_cache_repository import (  # noqa: E501
    SqlAlchemyGeorefReverseCacheRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_nominatim_reverse_cache_repository import (  # noqa: E501
    SqlAlchemyNominatimReverseCacheRepository,
)


def _coords() -> tuple[float, float]:
    # Coordenadas únicas por test: la clave es (lat, lon) redondeada a 4 decimales.
    sufijo = uuid.uuid4().int % 10_000
    return (-31.0 - sufijo / 10_000, -68.0 - sufijo / 10_000)


async def test_georef_cache_miss_put_y_hit_con_redondeo(db_session: AsyncSession) -> None:
    repo = SqlAlchemyGeorefReverseCacheRepository(db_session)
    lat, lon = _coords()
    assert await repo.get(lat, lon) is None

    ubicacion = UbicacionGeoref(
        provincia_nombre="San Juan",
        provincia_id="70",
        departamento_nombre="Capital",
        departamento_id="70028",
    )
    await repo.put(lat, lon, ubicacion)
    # Misma clave tras redondear a 4 decimales: hit; y el segundo put no pisa.
    await repo.put(lat + 0.00001, lon, None)

    cacheado = await repo.get(lat + 0.00001, lon)
    assert cacheado is not None
    assert cacheado.ubicacion == ubicacion


async def test_georef_cache_guarda_sin_cobertura(db_session: AsyncSession) -> None:
    repo = SqlAlchemyGeorefReverseCacheRepository(db_session)
    lat, lon = _coords()
    await repo.put(lat, lon, None)

    cacheado = await repo.get(lat, lon)
    assert cacheado is not None
    assert cacheado.ubicacion is None


async def test_nominatim_cache_miss_put_hit_y_sin_cobertura(db_session: AsyncSession) -> None:
    repo = SqlAlchemyNominatimReverseCacheRepository(db_session)
    lat, lon = _coords()
    assert await repo.get(lat, lon) is None

    await repo.put(lat, lon, UbicacionNominatim(provincia_nombre="Mendoza"))
    await repo.put(lat, lon, None)  # conflicto: se conserva el primero
    hit = await repo.get(lat, lon)
    assert hit is not None
    assert hit.ubicacion == UbicacionNominatim(provincia_nombre="Mendoza")

    lat2, lon2 = _coords()
    await repo.put(lat2, lon2, None)
    vacio = await repo.get(lat2, lon2)
    assert vacio is not None
    assert vacio.ubicacion is None


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
