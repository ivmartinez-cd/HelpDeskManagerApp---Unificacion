"""Caso de uso: parsear + enriquecer + analizar un texto de log HP."""

from __future__ import annotations

from dataclasses import dataclass

from src.modules.analisis_log_hp.domain.entities.incident import AnalysisResult
from src.modules.analisis_log_hp.domain.entities.log_event import EnrichedEvent
from src.modules.analisis_log_hp.domain.repositories.error_code_repository import (
    ErrorCodeRepository,
)
from src.modules.analisis_log_hp.domain.services.analysis_service import analyze_events
from src.modules.analisis_log_hp.domain.services.log_enrichment import enrich_events
from src.modules.analisis_log_hp.domain.services.log_parser import (
    ParserReport,
    normalize_log_text,
    parse_log_text,
)


@dataclass
class AnalyzeLogResult:
    report: ParserReport
    events: list[EnrichedEvent]
    analysis: AnalysisResult
    codes_new: list[str]


class AnalyzeLog:
    def __init__(self, error_code_repo: ErrorCodeRepository) -> None:
        self._repo = error_code_repo

    async def execute(self, raw_text: str) -> AnalyzeLogResult:
        normalized = normalize_log_text(raw_text)
        report = parse_log_text(normalized)
        unique_codes = list(dict.fromkeys(e.code for e in report.events))
        catalog = await self._repo.get_by_codes(unique_codes)
        events = enrich_events(report.events, catalog)
        analysis = analyze_events(events)
        codes_new = [c for c in unique_codes if c not in catalog]
        return AnalyzeLogResult(
            report=report, events=events, analysis=analysis, codes_new=codes_new
        )
