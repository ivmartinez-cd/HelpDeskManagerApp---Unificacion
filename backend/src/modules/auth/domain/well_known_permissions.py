from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

# Un solo lugar para este permiso: lo usan tanto el gate de los endpoints
# /admin/* como la guarda CANNOT_DEMOTE_SELF — que estén desincronizados
# sería un bug de seguridad silencioso.
MANAGE_ADMIN = Permission(ModuleKey("admin"), ActionKey("manage"))
