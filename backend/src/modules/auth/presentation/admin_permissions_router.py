import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.use_cases.get_user_permissions import (
    GetUserPermissions,
    GetUserPermissionsDependencies,
)
from src.modules.auth.application.use_cases.list_module_catalog import (
    ListModuleCatalog,
    ListModuleCatalogDependencies,
)
from src.modules.auth.application.use_cases.replace_user_permissions import (
    ReplaceUserPermissions,
    ReplaceUserPermissionsDependencies,
)
from src.modules.auth.domain.well_known_permissions import MANAGE_ADMIN
from src.modules.auth.infrastructure.repositories.sqlalchemy_module_catalog_repository import (
    SqlAlchemyModuleCatalogRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_permission_audit_repository import (
    SqlAlchemyPermissionAuditRepository,
)
from src.modules.auth.infrastructure.repositories.sqlalchemy_permission_repository import (
    SqlAlchemyPermissionRepository,
)
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.auth.presentation.schemas.catalog_schemas import ModuleCatalogResponse
from src.modules.auth.presentation.schemas.permission_schemas import (
    PermissionsResponse,
    ReplacePermissionsRequest,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])

_require_manage_admin = Depends(require_permission(MANAGE_ADMIN))


@router.get("/catalog/modules")
async def list_modules(
    _: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> list[ModuleCatalogResponse]:
    deps = ListModuleCatalogDependencies(catalog=SqlAlchemyModuleCatalogRepository(db))
    entries = await ListModuleCatalog(deps).execute()
    return [ModuleCatalogResponse.from_domain(entry) for entry in entries]


@router.get("/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: uuid.UUID,
    _: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> PermissionsResponse:
    deps = GetUserPermissionsDependencies(permissions=SqlAlchemyPermissionRepository(db))
    permissions = await GetUserPermissions(deps).execute(user_id)
    return PermissionsResponse.from_domain(permissions)


@router.put("/users/{user_id}/permissions")
async def replace_user_permissions(
    user_id: uuid.UUID,
    payload: ReplacePermissionsRequest,
    identity: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> PermissionsResponse:
    deps = ReplaceUserPermissionsDependencies(
        permissions=SqlAlchemyPermissionRepository(db),
        audit=SqlAlchemyPermissionAuditRepository(db),
    )
    await ReplaceUserPermissions(deps).execute(
        target_user_id=user_id,
        desired=payload.to_domain(),
        actor_user_id=identity.user.id,
    )
    permissions = await SqlAlchemyPermissionRepository(db).get_for_user(user_id)
    return PermissionsResponse.from_domain(permissions)
