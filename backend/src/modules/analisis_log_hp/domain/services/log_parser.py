"""Parser de logs HP — port exacto del legacy (log_parser.py).

Comportamientos no obvios portados textualmente (§5 de la caracterización):
- normalize_log_text: 2+ espacios → tab (el portal HP copia tabs como espacios).
- Meses en español mapeados a inglés antes de parsear la fecha.
- Hora H:mm sin zero-pad → zero-padded antes del strptime.
- Header detection solo en las primeras 3 líneas no vacías.
- Con 5 columnas tab-separated, la 6ª (help) se rellena con vacío.
- Fallback: columnas separadas por espacios si tab-split da < 6 columnas.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime

from src.modules.analisis_log_hp.domain.entities.log_event import LogEvent

logger = logging.getLogger(__name__)

MAX_LOGS_LENGTH = 2_000_000

_DATE_FORMAT = "%d-%b-%Y %H:%M:%S"
_ES_MONTHS = {
    "ene": "Jan", "feb": "Feb", "mar": "Mar", "abr": "Apr",
    "may": "May", "jun": "Jun", "jul": "Jul", "ago": "Aug",
    "sep": "Sep", "oct": "Oct", "nov": "Nov", "dic": "Dec",
}
_TYPE_MAP = {"error": "ERROR", "warning": "WARNING", "info": "INFO"}
_HEADER_KEYWORDS = {"tipo", "type", "código", "codigo", "fecha", "date"}


@dataclass(frozen=True)
class ParserError:
    line_number: int
    raw_line: str
    reason: str


@dataclass
class ParserReport:
    events: list[LogEvent]
    errors: list[ParserError]


def normalize_log_text(text: str) -> str:
    """Reemplaza 2+ espacios por tab en cada línea (§5.1)."""
    return "\n".join(re.sub(r" {2,}", "\t", line) for line in text.splitlines())


def parse_log_text(payload: str) -> ParserReport:
    if len(payload) > MAX_LOGS_LENGTH:
        payload = payload[:MAX_LOGS_LENGTH]
    events: list[LogEvent] = []
    errors: list[ParserError] = []
    non_empty = 0
    for idx, raw_line in enumerate(payload.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        non_empty += 1
        try:
            evt = _parse_line(line, is_candidate_header=non_empty <= 3)
            if evt is not None:
                events.append(evt)
        except ValueError as exc:
            if str(exc) == "Header row skipped":
                continue
            errors.append(ParserError(line_number=idx, raw_line=line, reason=str(exc)))
            logger.debug("Línea %d ignorada — %s | raw: %r", idx, exc, line)
    return ParserReport(events=events, errors=errors)


def _parse_line(line: str, is_candidate_header: bool) -> LogEvent | None:
    raw_parts = [s.strip() for s in line.split("\t")]
    parts = [p for p in raw_parts if p] if len(raw_parts) > 1 else raw_parts
    if len(parts) == 5:
        parts.append("")
    if len(parts) < 6:
        tokens = line.split()
        if len(tokens) >= 6:
            parts = [
                tokens[0], tokens[1],
                f"{tokens[2]} {tokens[3]}",
                tokens[4], tokens[5],
                " ".join(tokens[6:]) if len(tokens) > 6 else "",
            ]
        else:
            raise ValueError(
                "Se esperaban 6 columnas tab-separated o 6+ tokens separados por espacio"
            )
    if is_candidate_header and _looks_like_header(parts):
        raise ValueError("Header row skipped")
    return LogEvent(
        type=_normalize_type(parts[0]),
        code=parts[1],
        timestamp=_parse_timestamp(parts[2]),
        counter=_parse_counter(parts[3]),
        firmware=parts[4] or None,
        help_reference=parts[5] or None,
    )


def _parse_timestamp(value: str) -> datetime:
    value = value.strip()
    if " " not in value:
        raise ValueError("El timestamp debe incluir fecha y hora")
    date_part, time_part = value.split(" ", 1)
    try:
        day, month, year = date_part.split("-")
    except ValueError as exc:
        raise ValueError("La fecha debe ser DD-MMM-YYYY") from exc
    month = _ES_MONTHS.get(month.lower(), month)
    month = month[:1].upper() + month[1:].lower()
    time_str = time_part.strip()
    if time_str and time_str[1:2] == ":":  # H:mm sin zero-pad (§5.2)
        time_str = "0" + time_str
    try:
        return datetime.strptime(f"{day}-{month}-{year} {time_str}", _DATE_FORMAT)
    except ValueError as exc:
        raise ValueError(f"Timestamp inválido: {value!r}") from exc


def _parse_counter(value: str) -> int:
    cleaned = value.strip()
    if not cleaned.isdigit():
        raise ValueError("El contador debe ser un entero positivo")
    return int(cleaned)


def _normalize_type(value: str) -> str:
    result = _TYPE_MAP.get(value.strip().lower())
    if not result:
        raise ValueError(f"Tipo de evento no soportado: {value!r}")
    return result


def _looks_like_header(parts: list[str]) -> bool:
    if not parts:
        return False
    joined = " ".join(parts).lower()
    return any(kw in joined for kw in _HEADER_KEYWORDS)
