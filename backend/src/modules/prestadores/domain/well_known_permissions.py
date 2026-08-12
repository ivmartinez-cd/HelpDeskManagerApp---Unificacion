from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("prestadores"), ActionKey("view"))
CREATE = Permission(ModuleKey("prestadores"), ActionKey("create"))
UPDATE = Permission(ModuleKey("prestadores"), ActionKey("update"))
DELETE = Permission(ModuleKey("prestadores"), ActionKey("delete"))
