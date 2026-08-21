"""Dependencias de permisos compartidas por los sub-routers de configuración."""

from fastapi import Depends

from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.liquidaciones.domain.well_known_permissions import EXPORT, UPDATE, VIEW

require_view = Depends(require_permission(VIEW))
require_update = Depends(require_permission(UPDATE))
require_export = Depends(require_permission(EXPORT))

# Catálogos chicos (prestadores/SPST/tarifarios/tabla KM) que la UI muestra
# completos, sin tabla paginada: el contrato sigue siendo Page[T] pero con un
# default generoso (mismo criterio que el módulo prestadores).
CATALOGO_SIZE = 500
