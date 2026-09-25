"""Acciones del módulo `personas` (ADR-040), sembradas por la migración del
catálogo con backfill desde vacaciones.manage / admin.manage:

- `view`: listado y ficha de personas.
- `update`: editar nombre, mail y color (la ficha y, si tiene, su cuenta). Cambiar
  el mail de alguien que entra a la app exige además `manage`, porque cambia con
  qué mail inicia sesión.
- `manage`: dar y quitar acceso a la app.
"""

from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

MODULE = ModuleKey("personas")

VIEW = Permission(MODULE, ActionKey("view"))
UPDATE = Permission(MODULE, ActionKey("update"))
MANAGE = Permission(MODULE, ActionKey("manage"))
