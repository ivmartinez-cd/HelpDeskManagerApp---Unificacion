"""Dependencias de permisos compartidas por los sub-routers de configuración."""

from fastapi import Depends

from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.liquidaciones.domain.well_known_permissions import UPDATE, VIEW

require_view = Depends(require_permission(VIEW))
require_update = Depends(require_permission(UPDATE))
