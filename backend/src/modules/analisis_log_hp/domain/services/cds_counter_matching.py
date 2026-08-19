"""Emparejar un incidente CD con la lectura de contador más relevante.

Port exacto de `find_counter_for_incident` del legacy
(`Printer-Logs-Analyzer/backend/application/services/cds_service.py`):
prioriza una toma de tipo "Informe S. Tecnico" dentro de la ventana del
incidente; si no hay, la lectura más reciente anterior al cierre (o a
fecha+30d si no cerró).
"""

from __future__ import annotations

from datetime import datetime, timedelta

_FMT_DT = "%d/%m/%Y %H:%M:%S"
_FMT_D = "%d/%m/%Y"


def find_counter_for_incident(
    counters: list[dict[str, str]], fecha_str: str, fecha_cierre_str: str | None
) -> str | None:
    fecha_dt = _parse_dt(fecha_str, _FMT_DT)
    if fecha_dt is None:
        return None
    upper = _parse_dt(fecha_cierre_str, _FMT_DT) if fecha_cierre_str else None
    if upper is None:
        upper = fecha_dt + timedelta(days=30)

    readings = _parse_readings(counters)
    if not readings:
        return None

    tecnico = [
        (dt, v) for dt, v, tipo in readings
        if tipo == "Informe S. Tecnico" and fecha_dt <= dt <= upper
    ]
    if tecnico:
        return max(tecnico, key=lambda r: r[0])[1]

    past = [(dt, v) for dt, v, _ in readings if dt <= upper]
    if past:
        return max(past, key=lambda r: r[0])[1]
    return None


def _parse_dt(raw: str | None, fmt: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, fmt)
    except ValueError:
        return None


def _parse_readings(counters: list[dict[str, str]]) -> list[tuple[datetime, str, str]]:
    parsed: list[tuple[datetime, str, str]] = []
    for c in counters:
        valor = c.get("Contador")
        if not valor:
            continue
        raw_date = c.get("FechaToma", "")
        dt = _parse_dt(raw_date, _FMT_D) or _parse_dt(raw_date, _FMT_DT)
        if dt is not None:
            parsed.append((dt, str(valor), c.get("TipoToma", "")))
    return parsed
