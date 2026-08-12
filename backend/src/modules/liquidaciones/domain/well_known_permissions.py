"""Acciones del módulo `liquidaciones`, ya sembradas en el catálogo de permisos
(`4c741806341e_seed_catalog.py`: view/create/update/approve/export) — is_enabled=False
hasta que exista frontend. `approve`/`export` quedan sin `Permission` propio todavía:
los agrega el caso de uso que primero los necesite (aprobación de liquidación,
exportación), no antes."""

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
