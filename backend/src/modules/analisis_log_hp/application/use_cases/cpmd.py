"""Casos de uso: catálogo de manuales de servicio CPMD."""

from __future__ import annotations

from src.modules.analisis_log_hp.domain.entities.cpmd_manual import CpmdManual
from src.modules.analisis_log_hp.domain.repositories.cpmd_manual_repository import (
    CpmdManualRepository,
)


class FindCpmdManual:
    def __init__(self, repo: CpmdManualRepository) -> None:
        self._repo = repo

    async def execute(self, model_family: str) -> CpmdManual | None:
        return await self._repo.find_by_model_family(model_family)


class GetCpmdManualById:
    def __init__(self, repo: CpmdManualRepository) -> None:
        self._repo = repo

    async def execute(self, manual_id: int) -> CpmdManual | None:
        return await self._repo.get_by_id(manual_id)


class UploadCpmdManual:
    def __init__(self, repo: CpmdManualRepository) -> None:
        self._repo = repo

    async def execute(self, *, keywords: list[str], label: str, filename: str) -> CpmdManual:
        return await self._repo.create(keywords=keywords, label=label, filename=filename)
