import uuid
from uuid import UUID

import pytest

from src.modules.auth.application.use_cases.dashboard_prefs import (
    GetDashboardPrefs,
    SaveDashboardPrefs,
)
from src.modules.auth.domain.entities.dashboard_prefs import DashboardPrefs
from src.modules.auth.domain.errors import InvalidDashboardPrefsError


class FakeDashboardPrefsRepository:
    def __init__(self) -> None:
        self.rows: dict[UUID, DashboardPrefs] = {}

    async def get(self, user_id: UUID) -> DashboardPrefs | None:
        return self.rows.get(user_id)

    async def upsert(self, prefs: DashboardPrefs) -> DashboardPrefs:
        self.rows[prefs.user_id] = prefs
        return prefs


async def test_get_devuelve_defaults_si_el_usuario_nunca_guardo() -> None:
    user_id = uuid.uuid4()

    prefs = await GetDashboardPrefs(FakeDashboardPrefsRepository()).execute(user_id)

    assert prefs == DashboardPrefs.default(user_id)


async def test_save_reemplaza_y_get_lo_devuelve() -> None:
    repo = FakeDashboardPrefsRepository()
    user_id = uuid.uuid4()

    await SaveDashboardPrefs(repo).execute(
        user_id=user_id, hidden_cards=["insumos"], initial_view="seguimiento"
    )
    await SaveDashboardPrefs(repo).execute(user_id=user_id, hidden_cards=[], initial_view="hoy")
    prefs = await GetDashboardPrefs(repo).execute(user_id)

    assert (prefs.hidden_cards, prefs.initial_view) == ((), "hoy")


async def test_save_no_mezcla_usuarios() -> None:
    repo = FakeDashboardPrefsRepository()
    a, b = uuid.uuid4(), uuid.uuid4()

    await SaveDashboardPrefs(repo).execute(user_id=a, hidden_cards=["sla-mes"], initial_view="hoy")

    assert (await GetDashboardPrefs(repo).execute(b)) == DashboardPrefs.default(b)


async def test_save_valida_por_la_entidad_antes_de_persistir() -> None:
    repo = FakeDashboardPrefsRepository()

    with pytest.raises(InvalidDashboardPrefsError):
        await SaveDashboardPrefs(repo).execute(
            user_id=uuid.uuid4(), hidden_cards=["Mayus"], initial_view="hoy"
        )
    assert repo.rows == {}
