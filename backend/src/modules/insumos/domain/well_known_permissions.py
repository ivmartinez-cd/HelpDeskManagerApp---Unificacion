from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("insumos"), ActionKey("view"))
# Cargar un pedido en Canal Directo crea un pedido REAL (dinero real) — es la acción
# "create" del catálogo, separada de view a propósito.
CREATE = Permission(ModuleKey("insumos"), ActionKey("create"))
