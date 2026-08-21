from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("wati"), ActionKey("view"))
# Fuerza un ciclo de sincronización contra la API de WATI a demanda (botón
# "Actualizar"): consume cuota del rate limit, no es solo lectura del cache.
UPDATE = Permission(ModuleKey("wati"), ActionKey("update"))
