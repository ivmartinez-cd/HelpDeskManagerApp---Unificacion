from collections.abc import Sequence
from uuid import UUID

from src.modules.auth.domain.entities.dashboard_prefs import DashboardPrefs
from src.modules.auth.domain.repositories.dashboard_prefs_repository import (
    DashboardPrefsRepository,
)


class GetDashboardPrefs:
    """Preferencias de Inicio del usuario logueado; si nunca guardó, los
    defaults (nada oculto, vista "hoy") — el frontend no distingue los casos."""

    def __init__(self, repo: DashboardPrefsRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: UUID) -> DashboardPrefs:
        return await self._repo.get(user_id) or DashboardPrefs.default(user_id)


class SaveDashboardPrefs:
    """Reemplaza las preferencias completas (PUT idempotente). El `user_id`
    viene siempre de la identidad de la sesión, nunca del body."""

    def __init__(self, repo: DashboardPrefsRepository) -> None:
        self._repo = repo

    async def execute(
        self, *, user_id: UUID, hidden_cards: Sequence[str], initial_view: str
    ) -> DashboardPrefs:
        prefs = DashboardPrefs(
            user_id=user_id, hidden_cards=tuple(hidden_cards), initial_view=initial_view
        )
        return await self._repo.upsert(prefs)
