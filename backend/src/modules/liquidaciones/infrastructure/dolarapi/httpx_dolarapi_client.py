"""Adapter de CotizacionHoyProvider — dolarapi.com, solo la cotización de hoy
del oficial (sin histórico). Usado únicamente para el mes en curso; una vez
que el mes cierra, ArgentinaDatos publica el valor definitivo y lo reemplaza."""

import logging
from datetime import date

import httpx

from src.modules.liquidaciones.domain.repositories.cotizaciones_dolar_externas import (
    CotizacionDiaria,
)
from src.shared.domain.errors import ExternalServiceError

_logger = logging.getLogger(__name__)

_URL = "https://dolarapi.com/v1/dolares/oficial"
_TIMEOUT_SECONDS = 15.0


class HttpxDolarApiClient:
    async def fetch_oficial_hoy(self) -> CotizacionDiaria:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
                response = await client.get(_URL)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            _logger.error("Fallo consultando dolarapi", exc_info=exc)
            raise ExternalServiceError("No se pudo obtener la cotización de dolarapi") from exc
        try:
            return CotizacionDiaria(
                fecha=date.fromisoformat(payload["fechaActualizacion"][:10]),
                compra=float(payload["compra"]),
                venta=float(payload["venta"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            _logger.error(
                "Respuesta inesperada de dolarapi", extra={"payload": payload}, exc_info=exc
            )
            raise ExternalServiceError("Respuesta inesperada de dolarapi") from exc
