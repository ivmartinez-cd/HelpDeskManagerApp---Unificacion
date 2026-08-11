"""Endpoints de configuración del módulo (parámetros de operación de app_settings).

No es una colección: es un objeto único de configuración, por eso no va paginado.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.application.dtos.results import Identity
from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.insumos.domain.well_known_permissions import UPDATE, VIEW
from src.modules.insumos.presentation.dependencies import (
    build_get_insumos_config,
    build_save_insumos_config,
)
from src.modules.insumos.presentation.schemas.config_schemas import (
    ConfigRequestBody,
    ConfigResponse,
    SaveConfigResponse,
)
from src.shared.infrastructure.database.session import get_db

router = APIRouter(prefix="/api/insumos", tags=["insumos"])

_require_view = Depends(require_permission(VIEW))
_require_update = Depends(require_permission(UPDATE))


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    _: Identity = _require_view,
    db: AsyncSession = Depends(get_db),
) -> ConfigResponse:
    """Parámetros de operación vigentes (umbrales, auto-carga, offline, alertas)."""
    return ConfigResponse.from_view(await build_get_insumos_config(db).execute())


@router.put("/config", response_model=SaveConfigResponse)
async def put_config(
    body: ConfigRequestBody,
    _: Identity = _require_update,
    db: AsyncSession = Depends(get_db),
) -> SaveConfigResponse:
    """Guarda los parámetros. Responde 200 siempre: los rangos inválidos viajan como
    ok=false + error para mostrar en el formulario, igual que en el legacy."""
    result = await build_save_insumos_config(db).execute(body.to_command())
    return SaveConfigResponse.from_result(result)
