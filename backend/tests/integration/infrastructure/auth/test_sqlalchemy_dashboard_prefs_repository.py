"""SqlAlchemyDashboardPrefsRepository contra Postgres real (upsert por user_id)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.domain.entities.dashboard_prefs import DashboardPrefs
from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.auth.infrastructure.repositories.sqlalchemy_dashboard_prefs_repository import (
    SqlAlchemyDashboardPrefsRepository,
)


async def _crear_usuario(db_session: AsyncSession) -> uuid.UUID:
    user = AppUser(
        email=f"{uuid.uuid4()}@test.local", full_name="Prefs Test", password_hash="x",
        is_superadmin=False,
    )
    db_session.add(user)
    await db_session.flush()
    return user.id


async def test_get_sin_fila_devuelve_none(db_session: AsyncSession) -> None:
    repo = SqlAlchemyDashboardPrefsRepository(db_session)

    assert await repo.get(uuid.uuid4()) is None


async def test_upsert_inserta_y_luego_pisa(db_session: AsyncSession) -> None:
    user_id = await _crear_usuario(db_session)
    repo = SqlAlchemyDashboardPrefsRepository(db_session)

    await repo.upsert(
        DashboardPrefs(user_id=user_id, hidden_cards=("insumos", "sla-mes"), initial_view="hoy")
    )
    await repo.upsert(
        DashboardPrefs(user_id=user_id, hidden_cards=("parque",), initial_view="seguimiento")
    )
    leido = await repo.get(user_id)

    assert leido is not None
    assert (leido.hidden_cards, leido.initial_view) == (("parque",), "seguimiento")


async def test_las_preferencias_son_por_usuario(db_session: AsyncSession) -> None:
    a = await _crear_usuario(db_session)
    b = await _crear_usuario(db_session)
    repo = SqlAlchemyDashboardPrefsRepository(db_session)

    await repo.upsert(
        DashboardPrefs(user_id=a, hidden_cards=("wati-pendientes",), initial_view="hoy")
    )

    assert await repo.get(b) is None
    leido = await repo.get(a)
    assert leido is not None and leido.hidden_cards == ("wati-pendientes",)
