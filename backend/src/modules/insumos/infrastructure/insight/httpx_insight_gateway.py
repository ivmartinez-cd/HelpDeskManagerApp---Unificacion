"""Adapter httpx del puerto InsightGateway — port de InsightApiClient del legacy.

Auth: no es API key simple — POST /login con `Authorization: Basic base64(key:secret)`
devuelve access_token + expires_in; se cachea con margen de refresco de 300 segundos,
protegido por un lock porque el poller y los endpoints comparten la misma instancia.

Reintentos SOLO en GET (429/5xx, backoff corto) — PATCH nunca: reintentar una mutación
arriesga efectos dobles (misma regla que el Retry del legacy, que excluía POST a
propósito). Timeout explícito obligatorio en toda llamada (caracterización §8).
"""

import asyncio
import base64
import logging
import time
from typing import Any

import httpx

from src.modules.insumos.domain.errors import RespuestaInesperadaDeInsightError
from src.modules.insumos.domain.repositories.insight_gateway import JsonDict
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

_TOKEN_REFRESH_MARGIN_SECONDS = 300
# (connect, read) del legacy: DEFAULT_TIMEOUT = (5, 30).
_TIMEOUT = httpx.Timeout(30.0, connect=5.0)
_RETRY_STATUSES = (429, 500, 502, 503, 504)
_GET_RETRY_BACKOFF_SECONDS = (0.5, 1.0, 2.0)


class HttpxInsightGateway:
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
        self._token_lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self._client.aclose()

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
            time.monotonic() + float(data["expires_in"]) - _TOKEN_REFRESH_MARGIN_SECONDS
        )
        logger.info("Insight API login OK, token válido por %s segundos", data["expires_in"])

    async def _ensure_token(self) -> str:
        async with self._token_lock:
            if self._token is None or time.monotonic() >= self._token_expires_at:
                await self._login()
            # _login() siempre deja el token seteado (o lanza).
            assert self._token is not None
            return self._token

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: JsonDict | None = None,
    ) -> httpx.Response:
        token = await self._ensure_token()
        headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
        try:
            return await self._client.request(
                method, f"{self._base_url}{path}", headers=headers, params=params, json=json_body
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
        for backoff in _GET_RETRY_BACKOFF_SECONDS:
            if resp.status_code not in _RETRY_STATUSES:
                break
            await asyncio.sleep(backoff)
            resp = await self._request("GET", path, params=params)
        self._raise_for_status(resp, path)
        return resp.json()

    async def _get_list(self, path: str, params: dict[str, Any] | None = None) -> list[JsonDict]:
        result = await self._get(path, params)
        if not isinstance(result, list):
            raise RespuestaInesperadaDeInsightError(path, result)
        return result

    async def _patch(self, path: str, body: JsonDict) -> JsonDict:
        # Sin reintentos a propósito: es una mutación.
        resp = await self._request("PATCH", path, json_body=body)
        self._raise_for_status(resp, path)
        result = resp.json()
        return result if isinstance(result, dict) else {"raw": result}

    # ------------------------------------------------------------------ API pública --

    async def ping(self) -> None:
        await self._ensure_token()

    async def get_customers(self) -> list[JsonDict]:
        return await self._get_list("/api/customers")

    async def get_devices(self, customer_id: int) -> list[JsonDict]:
        return await self._get_list(
            "/api/devices", params={"customerId": customer_id, "includeExtendedFields": "true"}
        )

    async def get_zones(self, customer_id: int) -> list[JsonDict]:
        return await self._get_list("/api/zones", params={"customerId": customer_id})

    async def get_monitors(self, customer_id: int) -> list[JsonDict]:
        return await self._get_list(
            "/api/monitors", params={"customerId": customer_id, "includeExtendedFields": "true"}
        )

    async def get_device_by_id(self, device_id: int) -> JsonDict:
        result = await self._get(
            "/api/devices/search",
            params={"q": f"deviceId:{device_id}", "includeExtendedFields": "true"},
        )
        if isinstance(result, list):
            if not result:
                raise ExternalServiceError(
                    f"Insight API no encontró el equipo deviceId={device_id}"
                )
            return dict(result[0])
        return dict(result) if isinstance(result, dict) else {"raw": result}

    async def get_device_consumables(self, device_id: int) -> list[JsonDict]:
        result = await self._get(f"/api/devices/{device_id}/consumables")
        if isinstance(result, dict) and isinstance(result.get("consumables"), list):
            return list(result["consumables"])
        return []

    async def get_consumable_history(
        self,
        device_id: int,
        consumable_index: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[JsonDict]:
        params: dict[str, Any] = {"consumableIndex": consumable_index}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        result = await self._get(f"/api/devices/{device_id}/consumables/history", params=params)
        if isinstance(result, dict) and isinstance(result.get("historySteps"), list):
            return list(result["historySteps"])
        return []

    async def get_consumable_requests(
        self,
        customer_id: int,
        workflow_status: str = "OUTSTANDING",
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[JsonDict]:
        params: dict[str, Any] = {"customerId": customer_id, "workflowStatus": workflow_status}
        if from_date is not None:
            params["fromDate"] = from_date
        if to_date is not None:
            params["toDate"] = to_date
        return await self._get_list("/api/consumable-requests", params=params)

    async def update_consumable_request(
        self,
        request_id: int,
        external_ref: str | None = None,
        status_update: str | None = None,
        comment: str | None = None,
    ) -> JsonDict:
        body: JsonDict = {}
        if external_ref is not None:
            body["externalRef"] = external_ref
        if status_update is not None:
            body["statusUpdate"] = status_update
        if comment is not None:
            body["comment"] = comment
        return await self._patch(f"/api/consumable-requests/{request_id}", body)

    async def get_device_alerts_history(
        self,
        device_id: int,
        alert_classes: list[str] | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        max_results: int | None = None,
    ) -> list[JsonDict]:
        params: dict[str, Any] = {}
        if alert_classes is not None:
            params["alertClasses"] = alert_classes
        if from_date is not None:
            params["fromDate"] = from_date
        if to_date is not None:
            params["toDate"] = to_date
        if max_results is not None:
            params["maxResults"] = max_results
        return await self._get_list(f"/api/devices/{device_id}/alerts/history", params=params)
