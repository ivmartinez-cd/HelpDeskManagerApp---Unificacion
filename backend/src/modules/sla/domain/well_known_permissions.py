from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("sla"), ActionKey("view"))
# Fuerza un refresh en vivo contra MERCURIO (botón "Actualizar") — es "update",
# no "view": dispara una consulta pesada a demanda, no solo lee el cache.
UPDATE = Permission(ModuleKey("sla"), ActionKey("update"))
