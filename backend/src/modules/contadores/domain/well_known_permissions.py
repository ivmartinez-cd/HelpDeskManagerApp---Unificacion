from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("contadores"), ActionKey("view"))
EXPORT = Permission(ModuleKey("contadores"), ActionKey("export"))
MANAGE = Permission(ModuleKey("contadores"), ActionKey("manage"))
