"""Sesión válida pero sin el grant → 403 por HTTP (ADR-029 §4). Hasta acá los
tests de integración solo cubrían el 401 sin sesión; este arma una identidad
autenticada reemplazando `get_current_identity` (sin DB: el catálogo también
va fake) y confirma que `require_permission` corta antes de llegar al caso de
uso. El camino positivo completo necesita DB y se cubre en unit
(tests/unit/presentation/auth/test_require_permission.py)."""

import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

import src.modules.auth.presentation.dependencies.permissions as perms
from src.modules.auth.application.dtos.results import Identity, PermissionView, UserView
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.infrastructure.database.session import get_db
from src.shared.presentation.app import app


class _FakeCatalog:
    def __init__(self, _db: Any) -> None:
        pass

    async def is_enabled(self, module: ModuleKey) -> bool:
        return True


def _identity(*grants: tuple[str, str]) -> Identity:
    return Identity(
        user=UserView(
            id=uuid.uuid4(),
            email="op@example.com",
            full_name="Operador",
            is_superadmin=False,
            color=None,
        ),
        permissions=frozenset(PermissionView(module=m, action=a) for m, a in grants),
        session_id=uuid.uuid4(),
    )


async def _no_db() -> AsyncIterator[None]:
    yield None


@pytest.fixture
def _sesion_sin_turnos(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(perms, "SqlAlchemyModuleCatalogRepository", _FakeCatalog)
    app.dependency_overrides[get_current_identity] = lambda: _identity(("insumos", "view"))
    app.dependency_overrides[get_db] = _no_db
    yield None
    app.dependency_overrides.pop(get_current_identity, None)
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.usefixtures("_sesion_sin_turnos")
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/turnos/casillas"),
        ("POST", "/api/turnos/casillas"),
        ("GET", "/api/turnos/grilla-variantes"),
        ("POST", "/api/turnos/intercambios"),
        ("GET", "/api/admin/users"),
    ],
)
async def test_sesion_valida_sin_grant_devuelve_403(method: str, path: str) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request(method, path, json={})

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
