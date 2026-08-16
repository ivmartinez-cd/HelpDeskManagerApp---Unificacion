"""Puerto de cálculo de distancias vía Google Maps Distance Matrix API."""

from typing import Protocol

IdaVuelta = tuple[float | None, float | None]


class GoogleMapsGateway(Protocol):
    async def distancias_km(
        self,
        origin: tuple[float, float],
        destinations: list[tuple[float, float]],
    ) -> list[float | None]:
        """Distancias en km desde un origen a N destinos (modo DRIVING).
        Devuelve `None` por destino cuando Google Maps no puede rutear."""
        ...

    async def distancias_km_ida_vuelta(
        self,
        base: tuple[float, float],
        destinos: list[tuple[float, float]],
    ) -> list[IdaVuelta]:
        """Ida (base→destino) y vuelta (destino→base) por destino, en km.
        La vuelta se mide como tramo real B→A — puede diferir de la ida por
        manos únicas o ruteo. `None` en el tramo que Google no pudo rutear."""
        ...
