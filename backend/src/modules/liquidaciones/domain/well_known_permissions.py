"""Acciones del módulo `liquidaciones`, sembradas en el catálogo de permisos.

Sembradas desde el inicio (`4c741806341e_seed_catalog.py`): view/create/update/approve/export.
`approve` y `export` no tenían Permission propio hasta ahora — los agrega el caso de uso
que primero los necesita (este archivo: Fase 2). `delete` es nueva y requiere la migración
de datos `<rev>_seed_liquidaciones_delete_permission.py`."""

from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

_MODULE = ModuleKey("liquidaciones")

VIEW = Permission(_MODULE, ActionKey("view"))
# Reanalizar reemplaza alertas/observaciones y enriquece incidentes — no es de solo
# lectura, mismo criterio que insumos (ver su well_known_permissions.py).
UPDATE = Permission(_MODULE, ActionKey("update"))
# Importar crea una liquidación + incidentes reales — separada de update, mismo
# criterio que insumos.CREATE.
CREATE = Permission(_MODULE, ActionKey("create"))
# Aprobar y observar usan el mismo permiso: ambas escriben en wsAyC como acción de
# revisión. La TL que puede aprobar puede también observar.
APPROVE = Permission(_MODULE, ActionKey("approve"))
# Anular (voidLiquidation en wsAyC) es destructivo — permiso separado de APPROVE.
# Requiere la migración `<rev>_seed_liquidaciones_delete_permission.py`.
DELETE = Permission(_MODULE, ActionKey("delete"))
# Exportar CSV de la configuración (prestadores/SPST/tarifarios/tabla KM) y el
# worklist de geovalidación. Sembrado desde el inicio pero sin enforcement hasta
# ADR-029: antes esos endpoints pedían solo `view`.
EXPORT = Permission(_MODULE, ActionKey("export"))
