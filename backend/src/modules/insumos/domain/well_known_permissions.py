from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("insumos"), ActionKey("view"))
# Cargar un pedido en Canal Directo crea un pedido REAL (dinero real) — es la acción
# "create" del catálogo, separada de view a propósito.
CREATE = Permission(ModuleKey("insumos"), ActionKey("create"))
# Cambiar la configuración mueve los umbrales del auto-loader real (un `autoloadMaxDays`
# alto vuelve elegible casi toda la cola pendiente): es "update", no "view". El legacy
# exponía este PUT sin autenticación — hallazgo #2 de su SEGURIDAD_PENDIENTE.md.
UPDATE = Permission(ModuleKey("insumos"), ActionKey("update"))
# Borrar un equipo del catálogo y del portal SDS — irreversible. Ver ADR-008.
DELETE = Permission(ModuleKey("insumos"), ActionKey("delete"))
