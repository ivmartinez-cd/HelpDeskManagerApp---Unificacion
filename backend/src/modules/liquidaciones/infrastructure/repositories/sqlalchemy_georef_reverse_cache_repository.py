"""Implementación Postgres del puerto GeorefReverseCacheRepository."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.repositories.georef_reverse_cache_repository import (
    ReverseCacheado,
)
from src.modules.liquidaciones.domain.repositories.georeferenciacion_gateway import (
    UbicacionGeoref,
)
from src.modules.liquidaciones.infrastructure.models.georef_reverse_cache_model import (
    GeorefReverseCacheModel,
)

_PRECISION = 4  # ~11 m — más que suficiente para no perder cobertura real


def _clave(lat: float, lon: float) -> tuple[float, float]:
    return (round(lat, _PRECISION), round(lon, _PRECISION))


class SqlAlchemyGeorefReverseCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, lat: float, lon: float) -> ReverseCacheado | None:
        lat_r, lon_r = _clave(lat, lon)
        stmt = select(GeorefReverseCacheModel).where(
            GeorefReverseCacheModel.lat_redondeada == lat_r,
            GeorefReverseCacheModel.lon_redondeada == lon_r,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        if row.provincia_nombre is None:
            return ReverseCacheado(ubicacion=None)
        return ReverseCacheado(
            ubicacion=UbicacionGeoref(
                provincia_nombre=row.provincia_nombre,
                provincia_id=row.provincia_id or "",
                departamento_nombre=row.departamento_nombre,
                departamento_id=row.departamento_id,
            )
        )

    async def put(self, lat: float, lon: float, ubicacion: UbicacionGeoref | None) -> None:
        lat_r, lon_r = _clave(lat, lon)
        stmt = (
            pg_insert(GeorefReverseCacheModel)
            .values(
                lat_redondeada=lat_r,
                lon_redondeada=lon_r,
                provincia_nombre=ubicacion.provincia_nombre if ubicacion else None,
                provincia_id=ubicacion.provincia_id if ubicacion else None,
                departamento_nombre=ubicacion.departamento_nombre if ubicacion else None,
                departamento_id=ubicacion.departamento_id if ubicacion else None,
            )
            .on_conflict_do_nothing(index_elements=["lat_redondeada", "lon_redondeada"])
        )
        await self._session.execute(stmt)
        await self._session.flush()
