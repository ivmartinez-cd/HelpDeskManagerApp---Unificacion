from typing import Protocol
from uuid import UUID

from src.modules.auth.domain.entities.dashboard_prefs import DashboardPrefs


class DashboardPrefsRepository(Protocol):
    async def get(self, user_id: UUID) -> DashboardPrefs | None: ...

    async def upsert(self, prefs: DashboardPrefs) -> DashboardPrefs: ...
