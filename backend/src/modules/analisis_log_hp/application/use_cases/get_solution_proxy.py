"""Caso de uso: proxy de contenido de solución HP (en vivo con caché fallback)."""

from __future__ import annotations

import logging

from src.modules.analisis_log_hp.domain.errors import ErrorCodeNotFoundError
from src.modules.analisis_log_hp.domain.repositories.error_code_repository import (
    ErrorCodeRepository,
)
from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import HpPortalGateway

logger = logging.getLogger(__name__)


class GetSolutionProxy:
    def __init__(
        self, error_code_repo: ErrorCodeRepository, portal: HpPortalGateway
    ) -> None:
        self._repo = error_code_repo
        self._portal = portal

    async def execute(self, code: str) -> str | None:
        record = await self._repo.get_by_code(code)
        if not record:
            raise ErrorCodeNotFoundError(code)
        if not record.solution_url:
            return record.solution_content
        try:
            return await self._portal.fetch_solution_content(record.solution_url)
        except Exception as exc:
            logger.warning(
                "solution_proxy: fallo fetch en vivo para %s, usando caché",
                code,
                exc_info=exc,
            )
            return record.solution_content
