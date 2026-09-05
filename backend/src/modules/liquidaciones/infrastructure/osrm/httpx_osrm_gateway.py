"""Adapter httpx del puerto de distancias sobre OSRM (OpenStreetMap), servicio
`table` con `annotations=distance` — alternativa gratuita a Google Distance
Matrix (decisión del usuario 2026-09-05; el rediseño del Asistente de KM la
había dejado registrada como pendiente, §4.g). Mismo contrato que
`HttpxGoogleMapsGateway`: ida base→destinos y vuelta destino→base en km, `None`
donde no hay ruta.

Dos requests por lote: `sources=0` (fila base→N) y `destinations=0` (columna
N→base). Pausa de cortesía entre requests: el servidor público de OSRM es un
demo sin SLA y sin auth; `osrm_base_url` permite apuntar a uno propio."""

import asyncio
import logging
from typing import Any

import httpx

from src.modules.liquidaciones.domain.repositories.google_maps_gateway import IdaVuelta
from src.shared.domain.errors import ExternalServiceError

_LOG = logging.getLogger(__name__)
_PAUSA_SEGUNDOS = 1.0


def _coords_path(puntos: list[tuple[float, float]]) -> str:
    # OSRM espera lon,lat (al revés que Google).
    return ";".join(f"{lon},{lat}" for lat, lon in puntos)


class HttpxOsrmGateway:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def distancias_km(
        self,
        origin: tuple[float, float],
        destinations: list[tuple[float, float]],
    ) -> list[float | None]:
        if not destinations:
            return []
        data = await self._table([origin, *destinations], {"sources": "0"})
        return _fila(data, 0)[1:]

    async def distancias_km_ida_vuelta(
        self,
        base: tuple[float, float],
        destinos: list[tuple[float, float]],
    ) -> list[IdaVuelta]:
        if not destinos:
            return []
        puntos = [base, *destinos]
        idas = _fila(await self._table(puntos, {"sources": "0"}), 0)[1:]
        await asyncio.sleep(_PAUSA_SEGUNDOS)
        vueltas = _columna(await self._table(puntos, {"destinations": "0"}), 0)[1:]
        return list(zip(idas, vueltas, strict=True))

    async def _table(self, puntos: list[tuple[float, float]], extra: dict[str, str]) -> Any:
        url = f"{self._base_url}/table/v1/driving/{_coords_path(puntos)}"
        params = {"annotations": "distance", **extra}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            _LOG.error("OSRM HTTP error", extra={"status": exc.response.status_code}, exc_info=exc)
            raise ExternalServiceError("Error HTTP al llamar OSRM (OpenStreetMap)") from exc
        except httpx.HTTPError as exc:
            _LOG.error("OSRM connection error", exc_info=exc)
            raise ExternalServiceError("Error de conexión con OSRM (OpenStreetMap)") from exc
        data = resp.json()
        if data.get("code") != "Ok":
            _LOG.error("OSRM code not Ok", extra={"code": data.get("code")})
            raise ExternalServiceError(f"OSRM: {data.get('code')}")
        return data


def _km(valor: Any) -> float | None:
    return None if valor is None else float(valor) / 1000.0


def _fila(data: dict[str, Any], i: int) -> list[float | None]:
    """`sources=i`: la única fila de `distances` es origen i → cada punto."""
    distancias = data.get("distances") or []
    return [_km(v) for v in distancias[0]] if distancias else []


def _columna(data: dict[str, Any], j: int) -> list[float | None]:
    """`destinations=j`: cada fila de `distances` tiene un solo valor, punto → j."""
    return [_km(fila[0]) if fila else None for fila in data.get("distances") or []]
