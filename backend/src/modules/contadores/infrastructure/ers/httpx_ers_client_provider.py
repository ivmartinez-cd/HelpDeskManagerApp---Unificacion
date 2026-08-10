from __future__ import annotations

import csv
import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

import httpx

from src.modules.contadores.domain.entities.ers_client import ErsClient
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


class HttpxErsClientProvider:
    """Implementación de ErsClientProvider usando httpx y renovación de token
    con Playwright para interactuar con Epson Remote Services (ERS)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def list_active_customers(self) -> list[ErsClient]:
        data = await self._ensure_token()
        url = f"{self._settings.epson_ers_base_url}/device_groups/"
        headers, cookies = self._build_request_params(data)
        timeout = httpx.Timeout(self._settings.epson_ers_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout, cookies=cookies) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code in (401, 403):
                    data = await self._ensure_token(force_refresh=True)
                    headers, cookies = self._build_request_params(data)
                    async with httpx.AsyncClient(timeout=timeout, cookies=cookies) as client2:
                        resp = await client2.get(url, headers=headers)
        except Exception as exc:
            raise ExternalServiceError(f"Error al conectar con ERS: {exc}") from exc

        if resp.status_code != 200:
            raise ExternalServiceError(
                f"Error al obtener grupos de ERS: {resp.status_code} - {resp.text}"
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
        data = await self._ensure_token()
        url = f"{self._settings.epson_ers_base_url}/device_groups/{group_id}/devices/"
        headers, cookies = self._build_request_params(data)
        timeout = httpx.Timeout(self._settings.epson_ers_timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout, cookies=cookies) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code in (401, 403):
                    data = await self._ensure_token(force_refresh=True)
                    headers, cookies = self._build_request_params(data)
                    async with httpx.AsyncClient(timeout=timeout, cookies=cookies) as client2:
                        resp = await client2.get(url, headers=headers)
        except Exception as exc:
            raise ExternalServiceError(f"Error al obtener dispositivos ERS: {exc}") from exc

        if resp.status_code != 200:
            raise ExternalServiceError(
                f"Error al obtener dispositivos ERS: {resp.status_code} - {resp.text}"
            )

        device_ids: list[str] = resp.json().get("devices", [])
        if not device_ids:
            raise ExternalServiceError(
                f"No se encontraron dispositivos en el grupo ERS '{group_name}'."
            )

        max_dt = parse_max_date(max_date)
        min_dt = max_dt - timedelta(days=30)

        async with httpx.AsyncClient(timeout=timeout, cookies=cookies) as client:
            rows = await collect_device_rows(
                client=client,
                headers=headers,
                base_url=self._settings.epson_ers_base_url,
                device_ids=device_ids,
                max_dt=max_dt,
                min_dt=min_dt,
                suma_color=suma_color,
            )

        if not rows:
            msg = (
                "No se encontraron contadores en el rango de fechas "
                f"para el cliente '{group_name}'."
            )
            raise ExternalServiceError(msg)

        date_str = max_date.split("T")[0].replace("-", "")
        safe_name = (
            "".join([c for c in group_name if c.isalnum() or c in (" ", "_")])
            .strip()
            .replace(" ", "_")
        )
        suffix = "_SumaColor" if suma_color else ""
        filename = f"EPSON_{safe_name}_{date_str}{suffix}_AutoCSV.csv"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "SERIE",
            "FECHA",
            "TIPO",
            "CLASE_10",
            "CONTADOR_10",
            "CLASE_20",
            "CONTADOR_20",
            "MOTIVO",
            "OBSERVACION",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)

        return str(output_path)

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

    def _build_request_params(
        self, token_data: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, str]]:
        token = token_data.get("token", "")
        headers = {
            "accept": "application/json, text/plain, */*",
            "authorization": token,
            "referer": "https://www.remote-services.epson.com/devices",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        cookies_list = token_data.get("cookies", [])
        cookies_dict = {
            c["name"]: c["value"]
            for c in cookies_list
            if "name" in c and "value" in c
        }
        return headers, cookies_dict
