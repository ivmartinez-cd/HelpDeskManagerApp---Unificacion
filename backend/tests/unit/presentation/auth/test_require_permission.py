"""`require_permission` (ADR-029 §4): fail-closed con sesión válida pero sin el
grant, paso con el grant exacto, superadmin saltea el grant pero no el
`module.is_enabled`. Se ejercita la dependencia directamente (la función
interna que FastAPI resolvería), con el repositorio de catálogo reemplazado:
acá no hay DB."""

import uuid
from typing import Any

import pytest

import src.modules.auth.presentation.dependencies.permissions as perms
from src.modules.auth.application.dtos.results import Identity, PermissionView, UserView
from src.modules.auth.domain.errors import ForbiddenError
from src.modules.turnos.domain.well_known_permissions import MANAGE, VIEW
from src.shared.domain.value_objects.module_key import ModuleKey


class _FakeCatalog:
    enabled: set[str] = {"turnos"}

    def __init__(self, _db: Any) -> None:
        pass

    async def is_enabled(self, module: ModuleKey) -> bool:
        return module.value in self.enabled


def _identity(*grants: tuple[str, str], superadmin: bool = False) -> Identity:
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


@pytest.fixture(autouse=True)
def _catalogo_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeCatalog.enabled = {"turnos"}
    monkeypatch.setattr(perms, "SqlAlchemyModuleCatalogRepository", _FakeCatalog)


async def test_sin_grant_es_403_aunque_la_sesion_sea_valida() -> None:
    check = perms.require_permission(VIEW)
    with pytest.raises(ForbiddenError):
        await check(identity=_identity(("insumos", "view")), db=None)


async def test_con_el_grant_exacto_pasa_y_devuelve_la_identidad() -> None:
    check = perms.require_permission(VIEW)
    identity = _identity(("turnos", "view"))
    assert await check(identity=identity, db=None) is identity


async def test_view_no_alcanza_para_manage() -> None:
    check = perms.require_permission(MANAGE)
    with pytest.raises(ForbiddenError):
        await check(identity=_identity(("turnos", "view")), db=None)


async def test_superadmin_pasa_sin_grant() -> None:
    check = perms.require_permission(MANAGE)
    identity = _identity(superadmin=True)
    assert await check(identity=identity, db=None) is identity


async def test_modulo_deshabilitado_es_403_incluso_para_superadmin() -> None:
    _FakeCatalog.enabled = set()
    check = perms.require_permission(VIEW)
    with pytest.raises(ForbiddenError):
        await check(identity=_identity(superadmin=True), db=None)
