from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.application.use_cases.list_module_catalog import (
    ListModuleCatalog,
    ListModuleCatalogDependencies,
)
from src.modules.auth.domain.value_objects.action_key import ActionKey
from src.modules.auth.domain.value_objects.module_key import ModuleKey
from src.modules.auth.domain.value_objects.permission import Permission
from src.modules.auth.infrastructure.repositories.sqlalchemy_module_catalog_repository import (
    SqlAlchemyModuleCatalogRepository,
)
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.auth.presentation.schemas.catalog_schemas import ModuleCatalogResponse
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])

_MANAGE_ADMIN = Permission(ModuleKey("admin"), ActionKey("manage"))
_require_manage_admin = Depends(require_permission(_MANAGE_ADMIN))


@router.get("/catalog/modules")
async def list_modules(
    _: Identity = _require_manage_admin,
    db: AsyncSession = Depends(get_db),
) -> list[ModuleCatalogResponse]:
    deps = ListModuleCatalogDependencies(catalog=SqlAlchemyModuleCatalogRepository(db))
    entries = await ListModuleCatalog(deps).execute()
    return [ModuleCatalogResponse.from_domain(entry) for entry in entries]
