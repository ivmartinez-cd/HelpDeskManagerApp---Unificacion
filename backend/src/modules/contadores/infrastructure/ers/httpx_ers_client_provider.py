from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import httpx

from src.modules.contadores.domain.entities.ers_client import ErsClient
from src.modules.contadores.infrastructure.csv.auto_csv_writer import (
    AutoCsvTarget,
    write_auto_csv,
)
from src.modules.contadores.infrastructure.ers.ers_device_telemetry import (
    collect_device_rows,
    parse_max_date,
)
from src.modules.contadores.infrastructure.ers.httpx_ers_token_refresher import (
    refresh_ers_token,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class _ErsSession:
    """Headers y cookies que salen del token cacheado; con ellos se firma cada request."""

    headers: dict[str, str]
    cookies: dict[str, str]


@dataclass(frozen=True)
class _MetersQuery:
    """Qué contadores pedir: los dispositivos del grupo y la ventana de 30 días
    que termina en `max_dt`."""

    device_ids: list[str]
    max_dt: datetime
    min_dt: datetime
    suma_color: bool

    @classmethod
    def build(cls, device_ids: list[str], max_date: str, suma_color: bool) -> _MetersQuery:
        max_dt = parse_max_date(max_date)
        return cls(device_ids, max_dt, max_dt - timedelta(days=30), suma_color)


class HttpxErsClientProvider:
    """Implementación de ErsClientProvider usando httpx contra Epson Remote
    Services (ERS); el token se renueva con httpx_ers_token_refresher."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def list_active_customers(self) -> list[ErsClient]:
        url = f"{self._settings.epson_ers_base_url}/device_groups/"
        resp, _ = await self._get_with_token_retry(
            url,
            error_prefix="Error al conectar con ERS",
            http_error_prefix="Error al obtener grupos de ERS",
        )
        items: list[dict[str, Any]] = resp.json().get("items", [])
        clients = [
            ErsClient(
                id=str(dg.get("id", "")),
                name=f"EPSON - {str(dg.get('name', '')).upper()}",
                status="ACTIVE",
            )
            for dg in items
            if dg.get("id")
        ]
        return sorted(clients, key=lambda c: c.name)

    async def export_meters_to_csv(
        self,
        *,
        group_id: str,
        group_name: str,
        max_date: str,
        output_dir: str,
        suma_color: bool = False,
    ) -> str:
        url = f"{self._settings.epson_ers_base_url}/device_groups/{group_id}/devices/"
        resp, session = await self._get_with_token_retry(
            url, error_prefix="Error al obtener dispositivos ERS"
        )
        device_ids: list[str] = resp.json().get("devices", [])
        if not device_ids:
            raise ExternalServiceError(
                f"No se encontraron dispositivos en el grupo ERS '{group_name}'."
            )
        query = _MetersQuery.build(device_ids, max_date, suma_color)
        rows = await self._collect_rows(session, query)
        if not rows:
            raise ExternalServiceError(
                "No se encontraron contadores en el rango de fechas "
                f"para el cliente '{group_name}'."
            )
        target = AutoCsvTarget(
            prefix="EPSON", name=group_name, max_date=max_date,
            output_dir=output_dir, suma_color=suma_color,
        )
        return str(write_auto_csv(rows, target))

    async def _get_with_token_retry(
        self, url: str, *, error_prefix: str, http_error_prefix: str | None = None
    ) -> tuple[httpx.Response, _ErsSession]:
        """GET autenticado; ante 401/403 renueva el token una vez y reintenta. Devuelve
        también la sesión vigente (la renovada, si hizo falta) para requests posteriores.
        `error_prefix` encabeza el error de conexión; `http_error_prefix` (por defecto
        el mismo) el de status distinto de 200."""
        session = self._build_session(await self._ensure_token())
        try:
            resp = await self._get(url, session)
            if resp.status_code in (401, 403):
                session = self._build_session(await self._ensure_token(force_refresh=True))
                resp = await self._get(url, session)
        except Exception as exc:
            raise ExternalServiceError(f"{error_prefix}: {exc}") from exc

        if resp.status_code != 200:
            prefix = http_error_prefix or error_prefix
            raise ExternalServiceError(f"{prefix}: {resp.status_code} - {resp.text}")
        return resp, session

    async def _get(self, url: str, session: _ErsSession) -> httpx.Response:
        timeout = httpx.Timeout(self._settings.epson_ers_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, cookies=session.cookies) as client:
            return await client.get(url, headers=session.headers)

    async def _collect_rows(
        self, session: _ErsSession, query: _MetersQuery
    ) -> list[dict[str, Any]]:
        timeout = httpx.Timeout(self._settings.epson_ers_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, cookies=session.cookies) as client:
            return await collect_device_rows(
                client=client,
                headers=session.headers,
                base_url=self._settings.epson_ers_base_url,
                device_ids=query.device_ids,
                max_dt=query.max_dt,
                min_dt=query.min_dt,
                suma_color=query.suma_color,
            )

    async def _ensure_token(self, force_refresh: bool = False) -> dict[str, Any]:
        file_path = Path(self._settings.epson_ers_token_file)
        if not force_refresh and file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    return cast(dict[str, Any], json.load(f))
            except Exception as exc:
                logger.warning(
                    "Token de ERS cacheado ilegible, se va a renovar",
                    extra={"token_file": str(file_path)},
                    exc_info=exc,
                )
        return await refresh_ers_token(
            token_file_path=str(file_path), settings=self._settings
        )

    def _build_session(self, token_data: dict[str, Any]) -> _ErsSession:
        headers = {
            "accept": "application/json, text/plain, */*",
            "authorization": token_data.get("token", ""),
            "referer": "https://www.remote-services.epson.com/devices",
            "user-agent": _BROWSER_USER_AGENT,
        }
        cookies_list = token_data.get("cookies", [])
        cookies = {
            c["name"]: c["value"]
            for c in cookies_list
            if "name" in c and "value" in c
        }
        return _ErsSession(headers=headers, cookies=cookies)
