from __future__ import annotations

import asyncio
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import httpx

from src.modules.contadores.domain.entities.ers_client import ErsClient
from src.modules.contadores.infrastructure.ers.playwright_ers_token_refresher import (
    refresh_ers_token_with_playwright,
)
from src.shared.domain.errors import ExternalServiceError
from src.shared.infrastructure.config.settings import Settings, get_settings


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

        max_dt = _parse_max_date(max_date)
        min_dt = max_dt - timedelta(days=30)

        sem = asyncio.Semaphore(5)
        async with httpx.AsyncClient(timeout=timeout, cookies=cookies) as client:
            tasks = [
                self._process_single_device(
                    client=client,
                    headers=headers,
                    device_id=did,
                    max_dt=max_dt,
                    min_dt=min_dt,
                    suma_color=suma_color,
                    sem=sem,
                )
                for did in device_ids
            ]
            results = await asyncio.gather(*tasks)

        rows = [r for r in results if r is not None]
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

    async def _process_single_device(
        self,
        *,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        device_id: str,
        max_dt: datetime,
        min_dt: datetime,
        suma_color: bool,
        sem: asyncio.Semaphore,
    ) -> dict[str, Any] | None:
        async with sem:
            upload_id, collected_dt_str = await self._get_latest_upload_id(
                client, headers, device_id, max_dt
            )
            if not upload_id or not collected_dt_str:
                return None

            try:
                clean_date = collected_dt_str.replace("Z", "").split(".")[0]
                device_dt = datetime.fromisoformat(clean_date)
                if device_dt < min_dt or device_dt > max_dt:
                    return None
                fecha_csv = device_dt.strftime("%d/%m/%Y")
            except Exception:
                fecha_csv = collected_dt_str[:10]

            details = await self._get_device_telemetry(client, headers, device_id, upload_id)
            if not details:
                return None

            serial = str(details.get("serial_number", ""))
            info = details.get("device_info_json", {})
            usage = info.get("UsageInfo", {})

            prt_marker = usage.get("PrtMarker") or {}
            total_pages = int(prt_marker.get("LC") or 0)

            marker_list = usage.get("Marker") or []
            marker = marker_list[0] if marker_list else {}
            color_pages = int(marker.get("TCP") or 0)

            if total_pages == 0:
                tp_mono = int(marker.get("TP") or 0)
                total_pages = tp_mono + color_pages

            is_color = color_pages > 0

            if is_color:
                if suma_color:
                    return {
                        "SERIE": serial,
                        "FECHA": fecha_csv,
                        "TIPO": 17,
                        "CLASE_10": 20,
                        "CONTADOR_10": total_pages,
                        "CLASE_20": "",
                        "CONTADOR_20": 0,
                        "MOTIVO": "",
                        "OBSERVACION": "Epson ERS - SumaColor",
                    }
                mono_calc = max(0, total_pages - color_pages)
                return {
                    "SERIE": serial,
                    "FECHA": fecha_csv,
                    "TIPO": 17,
                    "CLASE_10": 10,
                    "CONTADOR_10": mono_calc,
                    "CLASE_20": 20,
                    "CONTADOR_20": color_pages,
                    "MOTIVO": "",
                    "OBSERVACION": "Epson ERS",
                }
            return {
                "SERIE": serial,
                "FECHA": fecha_csv,
                "TIPO": 17,
                "CLASE_10": 10,
                "CONTADOR_10": total_pages,
                "CLASE_20": "",
                "CONTADOR_20": 0,
                "MOTIVO": "",
                "OBSERVACION": "Epson ERS",
            }

    async def _get_latest_upload_id(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        device_id: str,
        max_dt: datetime,
    ) -> tuple[str | None, str | None]:
        start_dt = max_dt - timedelta(days=60)
        url = f"{self._settings.epson_ers_base_url}/devices/{device_id}/statuses/"
        params = {
            "start_datetime": start_dt.strftime("%Y-%m-%dT00:00:00Z"),
            "end_datetime": max_dt.strftime("%Y-%m-%dT23:59:59Z"),
        }
        try:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                return None, None
            items = resp.json().get("items", [])
            if not items:
                return None, None
            return (
                cast(str, items[0].get("upload_id")),
                cast(str, items[0].get("collected_datetime")),
            )
        except Exception:
            return None, None

    async def _get_device_telemetry(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        device_id: str,
        upload_id: str,
    ) -> dict[str, Any] | None:
        url = (
            f"{self._settings.epson_ers_base_url}/devices/"
            f"{device_id}/statuses/{upload_id}/"
        )
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return None
            return cast(dict[str, Any], resp.json())
        except Exception:
            return None

    async def _ensure_token(self, force_refresh: bool = False) -> dict[str, Any]:
        file_path = Path(self._settings.epson_ers_token_file)
        if not force_refresh and file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    return cast(dict[str, Any], json.load(f))
            except Exception:
                pass
        return await refresh_ers_token_with_playwright(
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


def _parse_max_date(max_date: str) -> datetime:
    try:
        date_part = max_date.split("T")[0]
        if "-" in date_part:
            y, m, d = date_part.split("-")
            return datetime(int(y), int(m), int(d), 23, 59, 59)
        return datetime.fromisoformat(date_part).replace(hour=23, minute=59, second=59)
    except Exception:
        return datetime.now().replace(hour=23, minute=59, second=59)
