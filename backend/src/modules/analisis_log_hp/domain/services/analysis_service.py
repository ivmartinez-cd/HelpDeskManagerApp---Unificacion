"""Análisis de logs: agrupa eventos por código, un incidente por código.

Port exacto de application/services/analysis_service.py del legacy.
Sin reglas — la severidad del incidente es la máxima del grupo de eventos.
"""

from __future__ import annotations

from collections import defaultdict

from src.modules.analisis_log_hp.domain.entities.incident import AnalysisResult, Incident
from src.modules.analisis_log_hp.domain.entities.log_event import EnrichedEvent

_SEVERITY_SCORE: dict[str, int] = {"INFO": 1, "WARNING": 2, "ERROR": 3}


def analyze_events(events: list[EnrichedEvent]) -> AnalysisResult:
    """Un incidente por código, severidad = máxima del grupo."""
    ordered = sorted(events, key=lambda e: e.timestamp)
    if not ordered:
        return AnalysisResult(incidents=(), global_severity="INFO", events_count=0)

    by_code: dict[str, list[EnrichedEvent]] = defaultdict(list)
    for evt in ordered:
        by_code[evt.code].append(evt)

    incidents: list[Incident] = []
    for code, group in by_code.items():
        severity = max(
            (e.type.upper() for e in group),
            key=lambda s: _SEVERITY_SCORE.get(s, 0),
        )
        if severity not in _SEVERITY_SCORE:
            severity = "INFO"

        classification = code
        sds_link: str | None = None
        sds_solution_content: str | None = None
        for evt in group:
            if evt.code_description and evt.code_description.strip():
                classification = evt.code_description.strip()
                break
        for evt in group:
            if evt.code_solution_url and evt.code_solution_url.strip():
                sds_link = evt.code_solution_url.strip()
                sds_solution_content = evt.code_solution_content
                break

        start = group[0].timestamp
        end = group[-1].timestamp
        incidents.append(
            Incident(
                id=f"{code}-{start.isoformat()}",
                code=code,
                classification=classification,
                severity=severity,
                severity_weight=_SEVERITY_SCORE.get(severity, 0),
                occurrences=len(group),
                start_time=start,
                end_time=end,
                counter_range=(group[0].counter, group[-1].counter),
                sds_link=sds_link,
                sds_solution_content=sds_solution_content,
            )
        )

    global_severity = max(
        (e.type.upper() for e in ordered),
        key=lambda s: _SEVERITY_SCORE.get(s, 0),
    )
    if global_severity not in _SEVERITY_SCORE:
        global_severity = "INFO"

    return AnalysisResult(
        incidents=tuple(incidents),
        global_severity=global_severity,
        events_count=len(ordered),
    )
