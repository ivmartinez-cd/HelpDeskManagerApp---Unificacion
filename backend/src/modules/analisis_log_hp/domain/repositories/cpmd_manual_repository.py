"""Puerto: catálogo de manuales de servicio CPMD."""

from __future__ import annotations

from typing import Protocol

from src.modules.analisis_log_hp.domain.entities.cpmd_manual import CpmdManual


class CpmdManualRepository(Protocol):
    async def find_by_model_family(self, model_family: str) -> CpmdManual | None:
        """Primer manual cuyas `keywords` matchean como substring (case-insensitive)
        de `model_family` — mismo criterio que el legacy (§ver caracterización)."""
        ...

    async def get_by_id(self, manual_id: int) -> CpmdManual | None: ...

    async def create(self, *, keywords: list[str], label: str, filename: str) -> CpmdManual: ...
