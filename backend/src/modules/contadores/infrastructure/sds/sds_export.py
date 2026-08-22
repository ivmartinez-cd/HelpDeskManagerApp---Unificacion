"""Armado de las filas del CSV de contadores SDS (HP Insight) a partir de la
respuesta de `/api/devices/meters/latestbydate`. Separado de
httpx_sds_client_provider.py por tamaño (ARCHITECTURE_GUIDE §4): el provider se
queda con la comunicación HTTP y este módulo con el formato de salida."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MeterRowContext:
    """Lo que hace falta, además del contador en sí, para armar su fila de CSV."""

    customer_id: str
    serial_map: dict[Any, str]
    min_dt: datetime | None
    suma_color: bool


@dataclass(frozen=True)
class _Reading:
    serie: str
    fecha: str
    engine_cycles: int
    mono_pages: int
    colour_pages: int


def calculate_min_date(max_date: str) -> datetime | None:
    """30 días antes de `max_date`; None (no se filtra por fecha) si no se puede parsear."""
    try:
        date_part = max_date.split("T")[0]
        if "-" in date_part:
            y, m, d = date_part.split("-")
            max_dt = datetime(int(y), int(m), int(d))
        else:
            max_dt = datetime.fromisoformat(date_part)
        return max_dt - timedelta(days=30)
    except Exception as exc:
        logger.warning(
            "No se pudo calcular la fecha mínima SDS, no se va a filtrar por fecha",
            extra={"max_date": max_date},
            exc_info=exc,
        )
        return None


def build_meter_rows(
    meters: list[dict[str, Any]], ctx: MeterRowContext
) -> list[dict[str, Any]]:
    """Una fila por contador, descartando las lecturas anteriores a `ctx.min_dt`."""
    rows: list[dict[str, Any]] = []
    for device in meters:
        reading = _to_reading(device, ctx)
        if reading is not None:
            rows.append(_to_csv_row(reading, ctx.suma_color))
    return rows


def _to_reading(device: dict[str, Any], ctx: MeterRowContext) -> _Reading | None:
    fecha = _resolve_fecha(device, ctx)
    if fecha is None:
        return None
    return _Reading(
        serie=_resolve_serie(device, ctx.serial_map),
        fecha=fecha,
        engine_cycles=int(device.get("engineCycles") or 0),
        mono_pages=int(device.get("monoPages") or 0),
        colour_pages=int(device.get("colourPages") or 0),
    )


def _resolve_serie(device: dict[str, Any], serial_map: dict[Any, str]) -> str:
    """Número de serie del mapa de dispositivos; si no está, el deviceId crudo."""
    device_id = device.get("deviceId")
    return serial_map.get(device_id, str(device_id) if device_id is not None else "")


def _resolve_fecha(device: dict[str, Any], ctx: MeterRowContext) -> str | None:
    """Fecha de lectura en dd/mm/yyyy. None si es anterior a `ctx.min_dt` (la fila
    se descarta); el valor crudo si no se puede parsear."""
    raw_date = str(device.get("readingDate") or (str(device.get("readingDateTime", ""))[:10]))
    try:
        device_dt = datetime.strptime(raw_date, "%Y-%m-%d")
        if ctx.min_dt and device_dt < ctx.min_dt:
            return None
        return device_dt.strftime("%d/%m/%Y")
    except Exception as exc:
        logger.debug(
            "No se pudo parsear la fecha de un contador SDS, uso el valor crudo",
            extra={"customer_id": ctx.customer_id, "raw_date": raw_date},
            exc_info=exc,
        )
        return raw_date


@dataclass(frozen=True)
class _CsvCounters:
    """Columnas CLASE/CONTADOR de la fila; CLASE_20 vacía cuando no hay color."""

    clase_10: int
    contador_10: int
    clase_20: int | str = ""
    contador_20: int = 0


def _csv_counters(reading: _Reading, suma_color: bool) -> _CsvCounters:
    is_color = reading.colour_pages > 0
    if suma_color and is_color:
        # Suma color: un solo contador (clase 20) con el total de ciclos del motor.
        return _CsvCounters(clase_10=20, contador_10=reading.engine_cycles)
    return _CsvCounters(
        clase_10=10,
        contador_10=reading.mono_pages,
        clase_20=20 if is_color else "",
        contador_20=reading.colour_pages if is_color else 0,
    )


def _to_csv_row(reading: _Reading, suma_color: bool) -> dict[str, Any]:
    counters = _csv_counters(reading, suma_color)
    return {
        "SERIE": reading.serie,
        "FECHA": reading.fecha,
        "TIPO": 21,
        "CLASE_10": counters.clase_10,
        "CONTADOR_10": counters.contador_10,
        "CLASE_20": counters.clase_20,
        "CONTADOR_20": counters.contador_20,
        "MOTIVO": "",
        "OBSERVACION": "",
    }
