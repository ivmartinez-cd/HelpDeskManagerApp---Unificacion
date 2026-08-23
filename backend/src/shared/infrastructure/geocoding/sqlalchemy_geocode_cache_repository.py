"""Implementación Postgres del cache de geocodes (tabla geocode_cache)."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato
from src.shared.infrastructure.geocoding.geocode_cache_model import GeocodeCacheModel


class SqlAlchemyGeocodeCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, direccion_normalizada: str) -> list[GeocodeCandidato] | None:
        stmt = select(GeocodeCacheModel).where(
            GeocodeCacheModel.direccion_normalizada == direccion_normalizada
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return [_to_candidato(c) for c in row.candidatos]

    async def put(
        self, direccion_normalizada: str, candidatos: list[GeocodeCandidato]
    ) -> None:
        # Upsert atómico (ON CONFLICT), no select-then-insert: dos corridas
        # concurrentes geocodificando la misma dirección (dos sucursales
        # distintas con igual domicilio, o dos triggers manuales solapados)
        # no deben pisarse con un IntegrityError — el cache tolera la carrera.
        payload = [_to_dict(c) for c in candidatos]
        stmt = pg_insert(GeocodeCacheModel).values(
            direccion_normalizada=direccion_normalizada, candidatos=payload
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[GeocodeCacheModel.direccion_normalizada],
            set_={"candidatos": stmt.excluded.candidatos},
        )
        await self._session.execute(stmt)
        await self._session.flush()


def _to_dict(c: GeocodeCandidato) -> dict[str, Any]:
    return {
        "formatted_address": c.formatted_address,
        "latitud": c.latitud,
        "longitud": c.longitud,
        "location_type": c.location_type,
        "tipos": list(c.tipos),
        "partial_match": c.partial_match,
    }


def _to_candidato(d: dict[str, Any]) -> GeocodeCandidato:
    return GeocodeCandidato(
        formatted_address=d["formatted_address"],
        latitud=d["latitud"],
        longitud=d["longitud"],
        location_type=d["location_type"],
        tipos=tuple(d.get("tipos", [])),
        partial_match=bool(d.get("partial_match", False)),
    )
