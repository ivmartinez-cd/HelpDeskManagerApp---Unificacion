"""Parseo puro de las respuestas wsAyC para incidentes CD.

Mismo formato que insumos (JSON serializado dentro de strings SOAP) pero
puerto/parsing propios de este módulo — ver docstring de
`domain/repositories/wsayc_gateway.py` (ADR-018: la plomería del cliente se
comparte, el parsing no).
"""

from __future__ import annotations

import json

from src.modules.analisis_log_hp.domain.entities.cds_incident import CdsReplacement

_TEMPLATE_PREFIXES = ("Fallas:", "Mensaje de error:", "Observaciones:")


def safe_parse(raw: str | None) -> object:
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


def parse_machine(raw: str | None) -> tuple[str, str] | None:
    parsed = safe_parse(raw)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("Machine"), dict):
        return None
    machine = parsed["Machine"]
    machine_id = _text(machine, "id")
    return (machine_id, _text(machine, "empresa_id")) if machine_id else None


def parse_incidents(raw: str | None) -> list[dict[str, str]]:
    parsed = safe_parse(raw)
    if isinstance(parsed, dict):
        parsed = [parsed]
    if not isinstance(parsed, list):
        return []
    return [
        item["Incident"]
        for item in parsed
        if isinstance(item, dict) and isinstance(item.get("Incident"), dict)
    ]


def parse_counters(raw: str | None) -> list[dict[str, str]]:
    parsed = safe_parse(raw)
    if not isinstance(parsed, list):
        return []
    out = []
    for item in parsed:
        counter = item.get("Counter", item) if isinstance(item, dict) else None
        if isinstance(counter, dict):
            out.append(counter)
    return out


def parse_replacements(raw: str | None) -> list[CdsReplacement]:
    parsed = safe_parse(raw)
    if not isinstance(parsed, list):
        return []
    return [
        _to_replacement(item["Replacement"])
        for item in parsed
        if isinstance(item, dict) and isinstance(item.get("Replacement"), dict)
    ]


def parse_jobs(raw: str | None) -> list[str]:
    parsed = safe_parse(raw)
    if not isinstance(parsed, list):
        return []
    descriptions = (_job_description(item) for item in parsed)
    return [d for d in descriptions if d]


def _job_description(item: object) -> str | None:
    job = item.get("Job") if isinstance(item, dict) else None
    if not isinstance(job, dict):
        return None
    desc = _text(job, "Descripcion")
    if desc and desc != "." and len(desc) > 2 and not desc.startswith(_TEMPLATE_PREFIXES):
        return desc
    return None


def _to_replacement(data: dict[str, object]) -> CdsReplacement:
    try:
        cantidad = int(str(data.get("Cantidad") or 1))
    except (ValueError, TypeError):
        cantidad = 1
    return CdsReplacement(articulo=_text(data, "Articulo") or "Desconocido", cantidad=cantidad)


def _text(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    return str(value).strip() if value is not None else ""
