"""Caso de uso: validar un log y detectar códigos no catalogados."""

from __future__ import annotations

from src.modules.analisis_log_hp.domain.repositories.error_code_repository import (
    ErrorCodeRepository,
)
from src.modules.analisis_log_hp.domain.services.log_parser import (
    normalize_log_text,
    parse_log_text,
)


class ValidateLog:
    def __init__(self, error_code_repo: ErrorCodeRepository) -> None:
        self._repo = error_code_repo

    async def execute(self, raw_text: str) -> list[str]:
        """Retorna lista de códigos presentes en el log pero sin catalogar."""
        normalized = normalize_log_text(raw_text)
        report = parse_log_text(normalized)
        unique_codes = list(dict.fromkeys(e.code for e in report.events))
        catalog = await self._repo.get_by_codes(unique_codes)
        return [c for c in unique_codes if c not in catalog]
