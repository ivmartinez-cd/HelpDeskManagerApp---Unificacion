from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("preventivos"), ActionKey("view"))
UPDATE = Permission(ModuleKey("preventivos"), ActionKey("update"))
