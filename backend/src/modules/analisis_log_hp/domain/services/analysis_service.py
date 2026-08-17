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

    return AnalysisResult(
        incidents=tuple(_build_incident(code, group) for code, group in by_code.items()),
        global_severity=_max_severity(ordered),
        events_count=len(ordered),
    )


def _max_severity(events: list[EnrichedEvent]) -> str:
    severity = max(
        (e.type.upper() for e in events),
        key=lambda s: _SEVERITY_SCORE.get(s, 0),
    )
    return severity if severity in _SEVERITY_SCORE else "INFO"


def _primer_valor(group: list[EnrichedEvent], attr: str) -> EnrichedEvent | None:
    return next(
        (e for e in group if (getattr(e, attr) or "").strip()),
        None,
    )


def _build_incident(code: str, group: list[EnrichedEvent]) -> Incident:
    severity = _max_severity(group)
    con_descripcion = _primer_valor(group, "code_description")
    con_solucion = _primer_valor(group, "code_solution_url")
    descripcion = con_descripcion.code_description if con_descripcion else None
    solucion_url = con_solucion.code_solution_url if con_solucion else None
    start = group[0].timestamp
    return Incident(
        id=f"{code}-{start.isoformat()}",
        code=code,
        classification=descripcion.strip() if descripcion else code,
        severity=severity,
        severity_weight=_SEVERITY_SCORE.get(severity, 0),
        occurrences=len(group),
        start_time=start,
        end_time=group[-1].timestamp,
        counter_range=(group[0].counter, group[-1].counter),
        sds_link=solucion_url.strip() if solucion_url else None,
        sds_solution_content=con_solucion.code_solution_content if con_solucion else None,
    )
