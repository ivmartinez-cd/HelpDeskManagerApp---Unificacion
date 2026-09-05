from collections.abc import Awaitable, Callable

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity, PermissionView
from src.modules.auth.domain.errors import ForbiddenError
from src.modules.auth.infrastructure.repositories.sqlalchemy_module_catalog_repository import (
    SqlAlchemyModuleCatalogRepository,
)
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission
from src.shared.infrastructure.database.session import get_db

_Dependencia = Callable[..., Awaitable[Identity]]


def _view(permission: Permission) -> PermissionView:
    return PermissionView(module=permission.module.value, action=permission.action.value)


def _dependencia(module: ModuleKey, required: tuple[PermissionView, ...]) -> _Dependencia:
    """Fail-closed: sin ninguno de los grants -> 403. `is_superadmin` evita el
    chequeo de grant (ver ForbiddenError) pero no el de `module.is_enabled` —
    un módulo deshabilitado da 403 incluso para el superadmin."""

    async def _check(
        identity: Identity = Depends(get_current_identity),
        db: AsyncSession = Depends(get_db, scope="function"),
    ) -> Identity:
        catalog = SqlAlchemyModuleCatalogRepository(db)
        if not await catalog.is_enabled(module):
            raise ForbiddenError()
        if identity.user.is_superadmin or any(p in identity.permissions for p in required):
            return identity
        raise ForbiddenError()

    return _check


def require_permission(permission: Permission) -> _Dependencia:
    """Exige exactamente ese grant (módulo + acción)."""
    return _dependencia(permission.module, (_view(permission),))


def require_any_permission(*permissions: Permission) -> _Dependencia:
    """Alcanza con cualquiera de los grants, todos del mismo módulo (p. ej.
    `turnos.view` o `turnos.manage` para leer la grilla: `manage` no implica
    `view`, y sin esto un usuario con solo `manage` no podía ni listar)."""
    if not permissions:
        raise ValueError("require_any_permission necesita al menos un permiso")
    if len({p.module for p in permissions}) != 1:
        raise ValueError("require_any_permission: todos los permisos deben ser del mismo módulo")
    return _dependencia(permissions[0].module, tuple(_view(p) for p in permissions))
