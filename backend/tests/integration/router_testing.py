"""Soporte compartido de los tests de routers por HTTP (ASGITransport sobre la
app real, sin DB ni servicios externos). Mismo patrón que
test_analisis_log_hp_routers.py / test_require_permission_http.py: identidad
y catálogo de módulos fake vía `dependency_overrides`/monkeypatch; cada test
monkeypatchea además los factories/repos del módulo con fakes en memoria."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

import src.modules.auth.presentation.dependencies.permissions as perms
from src.modules.auth.application.dtos.results import Identity, PermissionView, UserView
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.app import app


class FakeCatalog:
    def __init__(self, _db: Any) -> None:
        pass

    async def is_enabled(self, module: ModuleKey) -> bool:
        return True


class FakeDb:
    """Sustituto de la `AsyncSession`: los routers solo la pasan a los
    factories (monkeypatcheados) o le hacen `commit()`."""

    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass


def make_identity(*grants: tuple[str, str], superadmin: bool = False) -> Identity:
    return Identity(
        user=UserView(
            id=uuid.uuid4(),
            email="op@example.com",
            full_name="Operador",
            is_superadmin=superadmin,
            color=None,
        ),
        permissions=frozenset(PermissionView(module=m, action=a) for m, a in grants),
        session_id=uuid.uuid4(),
    )


def client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def install_session(
    monkeypatch: pytest.MonkeyPatch,
    *grants: tuple[str, str],
    superadmin: bool = False,
    db: FakeDb | None = None,
) -> Identity:
    fake_db = db or FakeDb()

    async def _fake_db() -> AsyncIterator[FakeDb]:
        yield fake_db

    identity = make_identity(*grants, superadmin=superadmin)
    monkeypatch.setattr(perms, "SqlAlchemyModuleCatalogRepository", FakeCatalog)
    app.dependency_overrides[get_current_identity] = lambda: identity
    app.dependency_overrides[get_db] = _fake_db
    return identity


def current_identity() -> Identity:
    """La identidad instalada por `install_session` (para fakes que necesitan
    reconocer al usuario logueado, ej. un lookup de cartera por operador)."""
    return app.dependency_overrides[get_current_identity]()  # type: ignore[no-any-return]


def uninstall_session() -> None:
    app.dependency_overrides.pop(get_current_identity, None)
    app.dependency_overrides.pop(get_db, None)
