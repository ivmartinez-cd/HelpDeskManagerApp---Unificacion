"""Caso de uso: alta/edición de código en el catálogo.

Semántica COALESCE/NULLIF: campo vacío nunca pisa un valor existente (§5.4).
Si la URL trae contenido, se fetchea y se guarda como caché.
"""

from __future__ import annotations

import logging

from src.modules.analisis_log_hp.domain.entities.error_code import ErrorCode
from src.modules.analisis_log_hp.domain.repositories.error_code_repository import (
    ErrorCodeRepository,
)
from src.modules.analisis_log_hp.domain.repositories.hp_portal_gateway import HpPortalGateway

logger = logging.getLogger(__name__)


class UpsertErrorCode:
    def __init__(
        self, error_code_repo: ErrorCodeRepository, portal: HpPortalGateway
    ) -> None:
        self._repo = error_code_repo
        self._portal = portal

    async def execute(
        self,
        code: str,
        severity: str | None,
        description: str | None,
        solution_url: str | None,
    ) -> ErrorCode:
        solution_content: str | None = None
        if solution_url:
            try:
                solution_content = await self._portal.fetch_solution_content(solution_url)
            except Exception as exc:
                logger.warning(
                    "upsert_error_code: no se pudo fetchear contenido de %s",
                    solution_url,
                    exc_info=exc,
                )
        return await self._repo.upsert(
            code,
            severity=severity or None,
            description=description or None,
            solution_url=solution_url or None,
            solution_content=solution_content,
        )
