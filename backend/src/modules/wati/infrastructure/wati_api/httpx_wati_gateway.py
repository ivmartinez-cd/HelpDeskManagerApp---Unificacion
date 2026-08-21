"""Adapter httpx de la API V1 de WATI (solo lectura).

- Base verificada: `https://live-mt-server.wati.io/{tenant}/api/v1/...`.
- WATI (o el proxy corporativo) rechaza con 403 el User-Agent por defecto de
  las librerías Python; se manda uno propio.
- Rate limit publicado: 10 llamadas / 10 s en getContacts y getMessages. El
  gateway serializa las llamadas y deja `spacing_seconds` entre una y otra.
- `trust_env=True` (default de httpx): respeta HTTPS_PROXY, que es como sale
  a Internet la red de la empresa.
"""

import asyncio
import logging
import time
from typing import Any

import httpx

from src.modules.wati.domain.value_objects.evento import ContactoWati, EventoWati
from src.modules.wati.infrastructure.wati_api.mapping import contacto_from_json, evento_from_json
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

_USER_AGENT = "helpdesk-manager/1.0 (+wati-pendientes)"


class HttpxWatiGateway:
    def __init__(
        self,
        base_url: str,
        tenant_id: str,
        token: str,
        *,
        spacing_seconds: float = 1.1,
        timeout_seconds: float = 20.0,
    ) -> None:
        self._base = f"{base_url.rstrip('/')}/{tenant_id}/api/v1"
        self._configured = bool(tenant_id and token)
        self._spacing = spacing_seconds
        self._lock = asyncio.Lock()
        self._last_call = 0.0
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": _USER_AGENT,
            },
            timeout=httpx.Timeout(timeout_seconds, connect=5.0),
        )

    async def list_contactos_recientes(self, limite: int) -> list[ContactoWati]:
        data = await self._get("/getContacts", {"pageSize": limite, "pageNumber": 1})
        items = data.get("contact_list") or []
        return [c for c in (contacto_from_json(d) for d in items) if c is not None]

    async def get_eventos(self, wa_id: str, limite: int) -> list[EventoWati]:
        data = await self._get(f"/getMessages/{wa_id}", {"pageSize": limite, "pageNumber": 1})
        items = (data.get("messages") or {}).get("items") or []
        return [e for e in (evento_from_json(d) for d in items) if e is not None]

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self._configured:
            raise ExternalServiceError("WATI_TENANT_ID y WATI_API_TOKEN deben estar configurados")
        async with self._lock:
            await self._esperar_cupo()
            try:
                resp = await self._client.get(self._base + path, params=params)
            except httpx.HTTPError as exc:
                raise ExternalServiceError(f"WATI no responde: {exc}") from exc
            self._last_call = time.monotonic()
        if resp.status_code != 200:
            raise ExternalServiceError(
                f"WATI respondió {resp.status_code} en {path}",
                details={"status": resp.status_code, "body": resp.text[:200]},
            )
        body = resp.json()
        if not isinstance(body, dict):
            raise ExternalServiceError(f"WATI devolvió un cuerpo inesperado en {path}")
        return body

    async def _esperar_cupo(self) -> None:
        restante = self._spacing - (time.monotonic() - self._last_call)
        if restante > 0:
            await asyncio.sleep(restante)
