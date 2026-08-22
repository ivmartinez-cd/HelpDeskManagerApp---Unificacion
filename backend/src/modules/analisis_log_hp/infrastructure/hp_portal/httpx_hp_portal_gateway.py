"""Adapter httpx del portal web HP SDS (scraping async).

Port de SDSWebSession del legacy (requests síncrono) a httpx async.
Misma semántica de sesión: TTL 20 min, re-login con lock antes de expirar,
nunca re-login especulativo (ver insumos/httpx_sds_portal_gateway.py).

Operaciones portadas del legacy:
- search_device: serial → {id, model_name}
- fetch_event_logs_html: AJAX XML/CDATA con la tabla de eventos
- fetch_remote_ews_url: link one-time JWT al EWS del equipo
- get_hp_operations: tabla de operaciones HP Smart
- refresh_hp_cache: dispara actualización de caché HP
- fetch_solution_content: fetchea contenido de página de solución
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx
from lxml import html

from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import EventLogsResult
from src.modules.analisis_log_hp.infrastructure.hp_portal.html_parser import (
    extract_device_id,
    extract_help_urls,
    extract_model_name,
    html_to_tsv,
    parse_cache_refresh_form,
    parse_hp_operations,
)
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)

_BASE = "https://hp-sds-latam.insightportal.net/PortalWeb"
_ORIGIN = "https://hp-sds-latam.insightportal.net"
_SESSION_TTL = 20 * 60  # 20 minutos
_TIMEOUT = httpx.Timeout(30.0, connect=5.0)

CACHE_OP_TYPES = {
    "RefreshHPCloudDeviceActionCache",
    "RefreshHPCloudDeviceEventLogCache",
    "RefreshHPCloudDeviceConfigCache",
}


class HttpxHpPortalGateway:
    """Scraper del portal web SDS (una instancia por proceso, sesión persistida)."""

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._client = httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT)
        self._logged_in = False
        self._last_login: float = 0.0
        self._lock = asyncio.Lock()

    async def _login(self) -> None:
        if not self._username or not self._password:
            raise ExternalServiceError(
                "SDS_PORTAL_USERNAME y SDS_PORTAL_PASSWORD deben estar configurados"
            )
        await self._client.get(f"{_BASE}/login")
        resp = await self._client.post(
            f"{_BASE}/login",
            data={"username": self._username, "password": self._password},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": _ORIGIN,
                "Referer": f"{_BASE}/login",
            },
        )
        resp.raise_for_status()
        if "/login" in str(resp.url).lower():
            self._logged_in = False
            raise ExternalServiceError(
                "Login al portal SDS fallido — verificar SDS_PORTAL_USERNAME/SDS_PORTAL_PASSWORD"
            )
        self._logged_in = True
        self._last_login = time.monotonic()
        logger.info("Portal SDS login OK como %s", self._username)

    async def _ensure_session(self) -> None:
        now = time.monotonic()
        if self._logged_in and (now - self._last_login) < _SESSION_TTL:
            return
        async with self._lock:
            now = time.monotonic()
            if not self._logged_in or (now - self._last_login) >= _SESSION_TTL:
                await self._login()

    def _ajax_headers(self) -> dict[str, str]:
        return {
            "x-ekm-usage": "dialog",
            "x-requested-with": "XMLHttpRequest",
            "Accept": "*/*",
        }

    async def search_device(self, serial: str) -> dict[str, str]:
        await self._ensure_session()
        resp = await self._client.get(
            f"{_BASE}/search",
            params=[("src", "powerSearch"), ("q", serial), ("s", "devices")],
        )
        resp.raise_for_status()
        model_name = extract_model_name(resp.text)
        device_id = extract_device_id(str(resp.url), resp.text)
        if not device_id:
            raise ExternalServiceError(
                f"Equipo con serial {serial!r} no encontrado en el portal SDS"
            )
        return {"id": device_id, "model_name": model_name}

    async def fetch_event_logs(self, device_id: str, days: int = 30) -> EventLogsResult:
        from datetime import datetime, timedelta

        await self._ensure_session()
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        resp = await self._client.get(
            f"{_BASE}/devices/{device_id}/hpsmart/eventlogs",
            params=[
                ("from", date_from),
                ("eventLevel", "info"),
                ("eventLevel", "warning"),
                ("eventLevel", "error"),
            ],
            headers=self._ajax_headers(),
        )
        if resp.status_code != 200:
            raise ExternalServiceError(
                f"Error al obtener event logs del equipo {device_id} ({resp.status_code})"
            )
        raw = resp.text
        return EventLogsResult(tsv=html_to_tsv(raw), help_urls=extract_help_urls(raw))

    async def fetch_remote_ews_url(self, device_id: str) -> str | None:
        await self._ensure_session()
        resp = await self._client.get(
            f"{_BASE}/devices/{device_id}/hpsmart/ews",
            headers=self._ajax_headers(),
        )
        if resp.status_code != 200:
            raise ExternalServiceError(f"Error al obtener EWS remoto ({resp.status_code})")
        from src.modules.analisis_log_hp.infrastructure.hp_portal.html_parser import (
            _get_html_content,
        )
        html_content = _get_html_content(resp.text)
        tree = html.fromstring(html_content)
        links = tree.xpath('//div[@id="remoteEWSLaunchLink"]//a/@href')
        return links[0] if links else None

    async def get_hp_operations(self, device_id: str) -> list[dict[str, Any]]:
        await self._ensure_session()
        resp = await self._client.get(
            f"{_BASE}/devices/{device_id}/hpsmart/operations/refresh",
            headers=self._ajax_headers(),
        )
        if resp.status_code != 200:
            raise ExternalServiceError(f"Error al obtener operaciones HP ({resp.status_code})")
        return parse_hp_operations(resp.text)

    async def refresh_hp_cache(self, device_id: str) -> list[dict[str, Any]]:
        await self._ensure_session()
        baseline = await self._cache_ops_baseline(device_id)
        action_url, data = await self._load_cache_refresh_form(device_id)
        resp = await self._client.post(
            action_url, data=data,
            headers={
                "x-requested-with": "XMLHttpRequest",
                "Accept": "*/*",
                "Origin": _ORIGIN,
                "Referer": f"{_BASE}/devices/{device_id}/hpsmart",
            },
        )
        if resp.status_code not in (200, 204):
            raise ExternalServiceError(f"Error al disparar refresh de caché ({resp.status_code})")
        return baseline

    async def _cache_ops_baseline(self, device_id: str) -> list[dict[str, Any]]:
        """Operaciones de caché vigentes antes del refresh (vacío si no se pueden leer)."""
        try:
            baseline_ops = await self.get_hp_operations(device_id)
        except ExternalServiceError as exc:
            logger.warning(
                "refresh_hp_cache: sin baseline de operaciones device_id=%s", device_id,
                exc_info=exc,
            )
            baseline_ops = []
        return [
            {"operation": o["operation"], "sent": o.get("sent", "")}
            for o in baseline_ops
            if o.get("operation") in CACHE_OP_TYPES
        ]

    async def _load_cache_refresh_form(self, device_id: str) -> tuple[str, dict[str, str]]:
        """(action_url, data) del formulario de refresh de caché del panel hpsmart."""
        page_resp = await self._client.get(
            f"{_BASE}/devices/{device_id}/hpsmart",
            headers=self._ajax_headers(),
        )
        if page_resp.status_code != 200:
            raise ExternalServiceError(f"Error al cargar panel hpsmart ({page_resp.status_code})")
        return parse_cache_refresh_form(page_resp.text, origin=_ORIGIN)

    async def fetch_solution_content(self, url: str) -> str | None:
        await self._ensure_session()
        try:
            resp = await self._client.get(url)
            if resp.status_code == 200 and "login" not in str(resp.url).lower():
                return resp.text
            logger.warning(
                "fetch_solution_content: status=%s url_final=%s",
                resp.status_code, str(resp.url)[:80],
            )
        except httpx.HTTPError as exc:
            logger.warning("fetch_solution_content: error de red: %s", exc, exc_info=exc)
        return None
