import uuid
from dataclasses import dataclass

from src.modules.auth.domain.repositories.module_catalog_repository import (
    ModuleCatalogRepository,
)
from src.modules.auth.domain.repositories.permission_repository import PermissionRepository
from src.modules.auth.domain.value_objects.module_catalog_entry import ModuleCatalogEntry


@dataclass(frozen=True, slots=True)
class ListVisibleModulesDependencies:
    catalog: ModuleCatalogRepository
    permissions: PermissionRepository


class ListVisibleModules:
    """Arma el sidebar: módulos habilitados a los que el usuario tiene al
    menos un permiso. Distinto del catálogo completo de /admin/catalog
    (ese es para editar la matriz, este es "qué veo yo"). Un superadmin ve
    todo lo habilitado sin necesitar grants explícitos — mismo criterio que
    require_permission (ver ADR de ForbiddenError)."""

    def __init__(self, deps: ListVisibleModulesDependencies) -> None:
        self._deps = deps

    async def execute(
        self, *, user_id: uuid.UUID, is_superadmin: bool
    ) -> list[ModuleCatalogEntry]:
        catalog = await self._deps.catalog.list_all()
        enabled = [entry for entry in catalog if entry.is_enabled]
        if is_superadmin:
            return enabled
        permissions = await self._deps.permissions.get_for_user(user_id)
        visible_keys = permissions.modules()
        return [entry for entry in enabled if entry.key in visible_keys]
