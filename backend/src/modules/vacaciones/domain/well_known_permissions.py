"""Acciones del módulo `vacaciones`, sembradas en el catálogo de permisos
(view/create/update/approve en `4c741806341e_seed_catalog.py`, `manage` agregada
por `e8b2a5c91f47_vacaciones_schema.py`). Mapeo de los roles del legacy VacaSync
a la matriz usuario × módulo × acción (D4 del plan de migración):

- `view`: dashboard, calendario y lecturas (el alcance de datos lo resuelve
  `services/scoping.py` según el actor: propio / sector / global).
- `create`: ciclo de vida de las solicitudes propias (crear/editar/eliminar).
- `approve`: decidir solicitudes; si el usuario tiene sector asignado en
  `user_module_scope` solo decide su sector y nunca la propia.
- `manage`: rol admin del legacy — ABM de Gestión Humana, feriados, ciclos,
  exclusiones, config y los bypass (años pasados, ciclos cerrados, terceros).
- `update`: sembrada en el catálogo, sin uso en la Entrega 1.
"""

from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

MODULE = ModuleKey("vacaciones")

VIEW = Permission(MODULE, ActionKey("view"))
CREATE = Permission(MODULE, ActionKey("create"))
APPROVE = Permission(MODULE, ActionKey("approve"))
MANAGE = Permission(MODULE, ActionKey("manage"))
