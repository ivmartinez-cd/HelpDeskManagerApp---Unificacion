"""Puerto: análisis guardados."""

from typing import Any, Protocol
from uuid import UUID

from src.modules.analisis_log_hp.domain.entities.saved_analysis import SavedAnalysis


class SavedAnalysisRepository(Protocol):
    async def create(
        self,
        name: str,
        equipment_identifier: str | None,
        incidents: list[dict[str, Any]],
        global_severity: str,
        ai_diagnosis: str | None = None,
    ) -> SavedAnalysis: ...

    async def get_by_id(self, id: UUID) -> SavedAnalysis | None: ...

    async def list_page(self, page: int, size: int) -> tuple[list[SavedAnalysis], int]: ...

    async def update(
        self,
        id: UUID,
        name: str,
        incidents: list[dict[str, Any]],
        global_severity: str,
        ai_diagnosis: str | None = None,
    ) -> SavedAnalysis | None: ...

    async def delete(self, id: UUID) -> bool: ...
