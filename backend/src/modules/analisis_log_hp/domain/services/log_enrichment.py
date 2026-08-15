"""Enriquecimiento de eventos con el catálogo de códigos de error."""

from __future__ import annotations

import re

from src.modules.analisis_log_hp.domain.entities.error_code import ErrorCode
from src.modules.analisis_log_hp.domain.entities.log_event import EnrichedEvent, LogEvent


def enrich_events(
    events: list[LogEvent], catalog: dict[str, ErrorCode]
) -> list[EnrichedEvent]:
    enriched: list[EnrichedEvent] = []
    for evt in events:
        row = catalog.get(evt.code)
        enriched.append(
            EnrichedEvent(
                type=evt.type,
                code=evt.code,
                timestamp=evt.timestamp,
                counter=evt.counter,
                firmware=evt.firmware,
                help_reference=evt.help_reference,
                code_severity=row.severity if row else None,
                code_description=row.description if row else None,
                code_solution_url=row.solution_url if row else None,
                code_solution_content=row.solution_content if row else None,
            )
        )
    return enriched


def extract_serial_number(value: str | None) -> str | None:
    """Extrae el serial de formatos como 'Modelo (SERIAL)' (§5.5)."""
    if not value:
        return None
    val = value.strip()
    match = re.search(r"\(([^)]+)\)", val)
    if match:
        return match.group(1).strip().upper()
    return val.upper()
