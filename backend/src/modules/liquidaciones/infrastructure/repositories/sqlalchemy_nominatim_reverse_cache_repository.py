"""Implementación Postgres del puerto NominatimReverseCacheRepository."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.repositories.nominatim_gateway import UbicacionNominatim
from src.modules.liquidaciones.domain.repositories.nominatim_reverse_cache_repository import (
    NominatimCacheado,
)
from src.modules.liquidaciones.infrastructure.models.nominatim_reverse_cache_model import (
    NominatimReverseCacheModel,
)

_PRECISION = 4


def _clave(lat: float, lon: float) -> tuple[float, float]:
    return (round(lat, _PRECISION), round(lon, _PRECISION))


class SqlAlchemyNominatimReverseCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, lat: float, lon: float) -> NominatimCacheado | None:
        lat_r, lon_r = _clave(lat, lon)
        stmt = select(NominatimReverseCacheModel).where(
            NominatimReverseCacheModel.lat_redondeada == lat_r,
            NominatimReverseCacheModel.lon_redondeada == lon_r,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        if row.provincia_nombre is None:
            return NominatimCacheado(ubicacion=None)
        ubicacion = UbicacionNominatim(provincia_nombre=row.provincia_nombre)
        return NominatimCacheado(ubicacion=ubicacion)

    async def put(self, lat: float, lon: float, ubicacion: UbicacionNominatim | None) -> None:
        lat_r, lon_r = _clave(lat, lon)
        stmt = (
            pg_insert(NominatimReverseCacheModel)
            .values(
                lat_redondeada=lat_r,
                lon_redondeada=lon_r,
                provincia_nombre=ubicacion.provincia_nombre if ubicacion else None,
            )
            .on_conflict_do_nothing(index_elements=["lat_redondeada", "lon_redondeada"])
        )
        await self._session.execute(stmt)
        await self._session.flush()
