from collections.abc import Awaitable, Callable

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity, PermissionView
from src.modules.auth.domain.errors import ForbiddenError
from src.modules.auth.domain.value_objects.permission import Permission
from src.modules.auth.infrastructure.repositories.sqlalchemy_module_catalog_repository import (
    SqlAlchemyModuleCatalogRepository,
)
from src.modules.auth.presentation.dependencies.identity import get_current_identity
from src.shared.infrastructure.database.session import get_db


def require_permission(permission: Permission) -> Callable[..., Awaitable[Identity]]:
    """Fail-closed: sin grant -> 403. `is_superadmin` evita el chequeo de
    grant (ver ForbiddenError) pero no el de `module.is_enabled` — un módulo
    deshabilitado da 403 incluso para el superadmin."""
    required = PermissionView(module=permission.module.value, action=permission.action.value)

    async def _check(
        identity: Identity = Depends(get_current_identity),
        db: AsyncSession = Depends(get_db),
    ) -> Identity:
        catalog = SqlAlchemyModuleCatalogRepository(db)
        if not await catalog.is_enabled(permission.module):
            raise ForbiddenError()
        if identity.user.is_superadmin or required in identity.permissions:
            return identity
        raise ForbiddenError()

    return _check
