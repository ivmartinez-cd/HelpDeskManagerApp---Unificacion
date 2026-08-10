from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, cast

import httpx

logger = logging.getLogger(__name__)


async def collect_device_rows(
    *,
    client: httpx.AsyncClient,
    headers: dict[str, str],
    base_url: str,
    device_ids: list[str],
    max_dt: datetime,
    min_dt: datetime,
    suma_color: bool,
) -> list[dict[str, Any]]:
    """Recolecta, en paralelo (máximo 5 a la vez), la fila de CSV de cada
    dispositivo del grupo ERS — descarta los que no tienen telemetría o
    quedan fuera del rango de fechas."""
    sem = asyncio.Semaphore(5)
    tasks = [
        _process_single_device(
            client=client,
            headers=headers,
            base_url=base_url,
            device_id=did,
            max_dt=max_dt,
            min_dt=min_dt,
            suma_color=suma_color,
            sem=sem,
        )
        for did in device_ids
    ]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


def parse_max_date(max_date: str) -> datetime:
    try:
        date_part = max_date.split("T")[0]
        if "-" in date_part:
            y, m, d = date_part.split("-")
            return datetime(int(y), int(m), int(d), 23, 59, 59)
        return datetime.fromisoformat(date_part).replace(hour=23, minute=59, second=59)
    except Exception as exc:
        logger.warning(
            "No se pudo parsear max_date de ERS, usando hoy como fallback",
            extra={"max_date": max_date},
            exc_info=exc,
        )
        return datetime.now().replace(hour=23, minute=59, second=59)


async def _process_single_device(
    *,
    client: httpx.AsyncClient,
    headers: dict[str, str],
    base_url: str,
    device_id: str,
    max_dt: datetime,
    min_dt: datetime,
    suma_color: bool,
    sem: asyncio.Semaphore,
) -> dict[str, Any] | None:
    async with sem:
        upload_id, collected_dt_str = await _get_latest_upload_id(
            client, headers, base_url, device_id, max_dt
        )
        if not upload_id or not collected_dt_str:
            return None

        in_range, fecha_csv = _resolve_fecha_csv(collected_dt_str, min_dt, max_dt)
        if not in_range:
            return None

        details = await _get_device_telemetry(client, headers, base_url, device_id, upload_id)
        if not details:
            return None

        return _build_row(details, fecha_csv, suma_color)


def _resolve_fecha_csv(
    collected_dt_str: str, min_dt: datetime, max_dt: datetime
) -> tuple[bool, str]:
    """Devuelve (está_en_rango, fecha_formateada_para_csv).

    Si `collected_datetime` no se puede parsear, replica el comportamiento
    original: no filtra por rango (asume que está adentro) y usa un
    fallback crudo (primeros 10 caracteres) para la columna FECHA.
    """
    try:
        clean_date = collected_dt_str.replace("Z", "").split(".")[0]
        device_dt = datetime.fromisoformat(clean_date)
    except Exception as exc:
        logger.debug(
            "No se pudo parsear collected_datetime de ERS, uso fallback sin filtrar por rango",
            extra={"collected_datetime": collected_dt_str},
            exc_info=exc,
        )
        return True, collected_dt_str[:10]

    if device_dt < min_dt or device_dt > max_dt:
        return False, ""
    return True, device_dt.strftime("%d/%m/%Y")


def _build_row(details: dict[str, Any], fecha_csv: str, suma_color: bool) -> dict[str, Any]:
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
    base_row = {"SERIE": serial, "FECHA": fecha_csv, "TIPO": 17, "MOTIVO": "", "OBSERVACION": ""}

    if not is_color:
        return {
            **base_row,
            "CLASE_10": 10,
            "CONTADOR_10": total_pages,
            "CLASE_20": "",
            "CONTADOR_20": 0,
        }

    if suma_color:
        return {
            **base_row,
            "CLASE_10": 20,
            "CONTADOR_10": total_pages,
            "CLASE_20": "",
            "CONTADOR_20": 0,
            "OBSERVACION": "Epson ERS - SumaColor",
        }

    mono_calc = max(0, total_pages - color_pages)
    return {
        **base_row,
        "CLASE_10": 10,
        "CONTADOR_10": mono_calc,
        "CLASE_20": 20,
        "CONTADOR_20": color_pages,
        "OBSERVACION": "Epson ERS",
    }


async def _get_latest_upload_id(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    base_url: str,
    device_id: str,
    max_dt: datetime,
) -> tuple[str | None, str | None]:
    start_dt = max_dt - timedelta(days=60)
    url = f"{base_url}/devices/{device_id}/statuses/"
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
    except Exception as exc:
        logger.warning(
            "No se pudo obtener el último upload_id de ERS para un dispositivo",
            extra={"device_id": device_id},
            exc_info=exc,
        )
        return None, None


async def _get_device_telemetry(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    base_url: str,
    device_id: str,
    upload_id: str,
) -> dict[str, Any] | None:
    url = f"{base_url}/devices/{device_id}/statuses/{upload_id}/"
    try:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            return None
        return cast(dict[str, Any], resp.json())
    except Exception as exc:
        logger.warning(
            "No se pudo obtener telemetría de un dispositivo ERS",
            extra={"device_id": device_id, "upload_id": upload_id},
            exc_info=exc,
        )
        return None
