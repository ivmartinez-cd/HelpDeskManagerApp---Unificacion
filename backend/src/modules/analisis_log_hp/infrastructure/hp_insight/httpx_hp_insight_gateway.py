"""Adapter httpx del puerto HpInsightGateway para el módulo analisis-log-hp.

Misma Insight Portal API que insumos (mismo host y credenciales — §3.9 y §7
de la caracterización), pero implementado de forma independiente para no
importar desde modules/insumos (ADR-018, modules-are-independent).

Métodos nuevos que insumos no usa: search_by_serial, get_device_alerts_current,
get_device_meters_history.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from typing import Any

import httpx

from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

_TOKEN_REFRESH_MARGIN = 300
_TIMEOUT = httpx.Timeout(30.0, connect=5.0)
_RETRY_STATUSES = (429, 500, 502, 503, 504)
_RETRY_BACKOFF = (0.5, 1.0, 2.0)

JsonDict = dict[str, Any]


class HttpxHpInsightGateway:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_secret: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._api_secret = api_secret
        self._client = httpx.AsyncClient(timeout=_TIMEOUT, transport=transport)
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def _login(self) -> None:
        pair = f"{self._api_key}:{self._api_secret}".encode()
        headers = {
            "Authorization": f"Basic {base64.b64encode(pair).decode('ascii')}",
            "accept": "application/json",
        }
        try:
            resp = await self._client.post(f"{self._base_url}/login", headers=headers)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Error al autenticar en Insight API: {exc}") from exc
        if resp.status_code >= 400:
            raise ExternalServiceError(
                f"Login de Insight API devolvió {resp.status_code}: {resp.text[:500]}"
            )
        data = resp.json()
        self._token = str(data["access_token"])
        self._token_expires_at = (
            time.monotonic() + float(data["expires_in"]) - _TOKEN_REFRESH_MARGIN
        )

    async def _ensure_token(self) -> str:
        async with self._lock:
            if self._token is None or time.monotonic() >= self._token_expires_at:
                await self._login()
            assert self._token is not None
            return self._token

    async def _request(
        self, method: str, path: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        token = await self._ensure_token()
        headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
        try:
            return await self._client.request(
                method, f"{self._base_url}{path}", headers=headers, params=params
            )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Error de red contra Insight API en {path}: {exc}") from exc

    def _raise_for_status(self, resp: httpx.Response, path: str) -> None:
        if resp.status_code >= 400:
            raise ExternalServiceError(
                f"Insight API {path} devolvió {resp.status_code}: {resp.text[:500]}"
            )

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> object:
        resp = await self._request("GET", path, params=params)
        for backoff in _RETRY_BACKOFF:
            if resp.status_code not in _RETRY_STATUSES:
                break
            await asyncio.sleep(backoff)
            resp = await self._request("GET", path, params=params)
        self._raise_for_status(resp, path)
        return resp.json()

    async def _get_list(self, path: str, params: dict[str, Any] | None = None) -> list[JsonDict]:
        result = await self._get(path, params)
        if not isinstance(result, list):
            logger.warning("Insight API %s: se esperaba lista, se recibió %s", path, type(result))
            return []
        return result

    async def search_by_serial(self, serial: str) -> JsonDict | None:
        result = await self._get(
            "/api/devices/search",
            params={"q": f"serial:{serial}", "includeExtendedFields": "true"},
        )
        if isinstance(result, list):
            return dict(result[0]) if result else None
        if isinstance(result, dict):
            return dict(result)
        return None

    async def get_device_consumables(self, device_id: int) -> list[JsonDict]:
        result = await self._get(f"/api/devices/{device_id}/consumables")
        if isinstance(result, dict) and isinstance(result.get("consumables"), list):
            return list(result["consumables"])
        return []

    async def get_device_alerts_current(self, device_id: int) -> list[JsonDict]:
        return await self._get_list(f"/api/devices/{device_id}/alerts/current")

    async def get_device_alerts_history(
        self,
        device_id: int,
        from_date: str | None = None,
        to_date: str | None = None,
        max_results: int | None = None,
    ) -> list[JsonDict]:
        params: dict[str, Any] = {}
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date
        if max_results:
            params["maxResults"] = max_results
        return await self._get_list(f"/api/devices/{device_id}/alerts/history", params=params)

    async def get_device_meters_history(
        self, device_id: int, days: int = 90
    ) -> list[JsonDict]:
        return await self._get_list(
            f"/api/devices/{device_id}/meters/history",
            params={"days": days},
        )

    async def get_devices(self, customer_id: int) -> list[JsonDict]:
        return await self._get_list(
            "/api/devices",
            params={"customerId": customer_id, "includeExtendedFields": "true"},
        )

    async def get_customers(self) -> list[JsonDict]:
        return await self._get_list("/api/customers")
