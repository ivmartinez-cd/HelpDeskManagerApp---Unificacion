"""Adapter del puerto `ClasificadorIA` sobre la API REST de Gemini (httpx).

Mismo pedido que el legacy con `@google/genai`: salida JSON con schema,
`thinkingBudget` (1 es el mínimo que aceptan los modelos 3.x; 0 da 400) y sin
temperature (deprecada en 3.x: el determinismo lo pide el prompt). Por cada
modelo (principal y fallback) hay 1 reintento ante errores transitorios; si
fallan todos, `ExternalServiceError` y el lote queda pendiente."""

import asyncio
import logging
import random
from typing import Any

import httpx

from src.modules.reporte_incidentes.domain.errors import IaNoConfiguradaError
from src.modules.reporte_incidentes.domain.repositories.clasificador_ia import RespuestaIA
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

_URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
_TRANSITORIOS = {429, 500, 502, 503, 504}
_REINTENTOS = 1
_ESPERA_BASE_SEGUNDOS = 0.4
_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "i": {"type": "INTEGER"},
            "categoria": {"type": "STRING"},
            "subcategoria": {"type": "STRING"},
            "confianza": {"type": "STRING"},
        },
        "required": ["i", "categoria", "subcategoria", "confianza"],
    },
}


class GeminiClasificador:
    def __init__(
        self, api_key: str, modelos: tuple[str, ...], opciones: tuple[int, float]
    ) -> None:
        """`modelos` = principal y fallback; `opciones` = (thinking_budget, timeout)."""
        self._api_key = api_key
        self._modelos = tuple(dict.fromkeys(m for m in modelos if m))
        self._thinking_budget, self._timeout = opciones

    @property
    def configurado(self) -> bool:
        return bool(self._api_key)

    async def clasificar(self, prompt: str) -> RespuestaIA:
        if not self.configurado:
            raise IaNoConfiguradaError()
        ultimo: Exception | None = None
        for modelo in self._modelos:
            try:
                return await self._con_reintento(modelo, prompt)
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                ultimo = exc
                logger.warning("Gemini %s no disponible; pruebo el siguiente", modelo,
                               extra={"modelo": modelo}, exc_info=exc)
        raise ExternalServiceError(
            "La IA no respondió (todos los modelos fallaron). Probá de nuevo en unos minutos."
        ) from ultimo

    async def _con_reintento(self, modelo: str, prompt: str) -> RespuestaIA:
        for intento in range(_REINTENTOS + 1):
            try:
                return await self._pedir(modelo, prompt)
            except httpx.HTTPStatusError as exc:
                if intento == _REINTENTOS or exc.response.status_code not in _TRANSITORIOS:
                    raise
            except httpx.TransportError:
                if intento == _REINTENTOS:
                    raise
            await asyncio.sleep(_ESPERA_BASE_SEGUNDOS * 2**intento + random.random() * 0.2)
        raise AssertionError("inalcanzable")

    async def _pedir(self, modelo: str, prompt: str) -> RespuestaIA:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            respuesta = await client.post(
                _URL.format(modelo=modelo),
                headers={"x-goog-api-key": self._api_key},
                json=self._cuerpo(prompt),
            )
        respuesta.raise_for_status()
        return _a_respuesta(respuesta.json(), modelo)

    def _cuerpo(self, prompt: str) -> dict[str, Any]:
        return {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _SCHEMA,
                "thinkingConfig": {"thinkingBudget": self._thinking_budget},
            },
        }


def _a_respuesta(datos: dict[str, Any], modelo: str) -> RespuestaIA:
    partes = datos["candidates"][0]["content"]["parts"]
    uso = datos.get("usageMetadata", {})
    return RespuestaIA(
        texto="".join(p.get("text", "") for p in partes if not p.get("thought")),
        modelo=modelo,
        tokens_entrada=int(uso.get("promptTokenCount", 0)),
        tokens_salida=int(uso.get("candidatesTokenCount", 0)),
    )
