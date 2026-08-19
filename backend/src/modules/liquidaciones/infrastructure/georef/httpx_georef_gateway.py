"""Adapter httpx del puerto GeoreferenciacionGateway — API Georef del Estado
argentino (gratuita, sin auth). Backoff acotado (máximo 2 reintentos, 1s/2s)
SOLO ante 429/5xx — servicio público, no hay que rendirse al primer hiccup
transitorio, pero tampoco reintentar en loop si está realmente caído."""

import asyncio
import logging
from typing import Any

import httpx

from src.modules.liquidaciones.domain.repositories.georeferenciacion_gateway import (
    UbicacionGeoref,
)
from src.shared.domain.errors import ExternalServiceError

_LOG = logging.getLogger(__name__)
_BASE_URL = "https://apis.datos.gob.ar/georef/api"
_TIMEOUT_SECONDS = 30.0
_REINTENTOS_BACKOFF = (1.0, 2.0)


class HttpxGeorefGateway:
    def __init__(
        self, base_url: str = _BASE_URL, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        """`transport` inyectable para tests (`httpx.MockTransport`) — en
        producción `None` usa el transporte real de red."""
        self._base_url = base_url
        self._transport = transport

    async def reverse(self, lat: float, lon: float) -> UbicacionGeoref | None:
        data = await self._get("/ubicacion", {"lat": lat, "lon": lon})
        ubicacion = data.get("ubicacion", {})
        provincia = ubicacion.get("provincia") or {}
        if not provincia.get("nombre"):
            return None
        departamento = ubicacion.get("departamento") or {}
        return UbicacionGeoref(
            provincia_nombre=provincia["nombre"],
            provincia_id=provincia["id"],
            departamento_nombre=departamento.get("nombre"),
            departamento_id=departamento.get("id"),
        )

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        intentos = (0.0, *_REINTENTOS_BACKOFF)
        ultimo_error: Exception | None = None
        for espera in intentos:
            if espera:
                await asyncio.sleep(espera)
            try:
                return await self._request(path, params)
            except _ReintentableError as exc:
                ultimo_error = exc
                _LOG.warning(
                    "Georef reintentable, reintentando", extra={"path": path, "status": exc.status}
                )
        _LOG.error("Georef sin respuesta tras reintentos", extra={"path": path})
        raise ExternalServiceError(
            f"Georef: sin respuesta tras reintentos en {path}"
        ) from ultimo_error

    async def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT_SECONDS, transport=self._transport
            ) as client:
                resp = await client.get(f"{self._base_url}{path}", params=params)
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise _ReintentableError(resp.status_code)
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            _LOG.error(
                "Georef HTTP error", extra={"status": exc.response.status_code}, exc_info=exc
            )
            raise ExternalServiceError(f"Error HTTP al llamar Georef {path}") from exc
        except httpx.HTTPError as exc:
            _LOG.error("Georef connection error", extra={"path": path}, exc_info=exc)
            raise ExternalServiceError(f"Error de conexión con Georef {path}") from exc
        return resp.json()  # type: ignore[no-any-return]


class _ReintentableError(Exception):
    def __init__(self, status: int) -> None:
        super().__init__(f"Georef status reintentable: {status}")
        self.status = status
