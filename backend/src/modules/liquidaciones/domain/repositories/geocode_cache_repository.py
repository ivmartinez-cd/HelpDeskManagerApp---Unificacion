"""Puerto del cache de geocodes por dirección normalizada.

Una dirección ya consultada no se vuelve a pedir a Google (la key es paga y
corporativa): `get` distingue miss (`None`) de "Google no encontró nada"
(lista vacía cacheada), para que un ZERO_RESULTS tampoco se re-consulte."""

from typing import Protocol

from src.modules.liquidaciones.domain.repositories.geocoding_gateway import GeocodeCandidato


class GeocodeCacheRepository(Protocol):
    async def get(self, direccion_normalizada: str) -> list[GeocodeCandidato] | None:
        """`None` = nunca consultada; lista (posiblemente vacía) = cacheada."""
        ...

    async def put(
        self, direccion_normalizada: str, candidatos: list[GeocodeCandidato]
    ) -> None: ...
