from dataclasses import dataclass

from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey


@dataclass(frozen=True, slots=True)
class Permission:
    module: ModuleKey
    action: ActionKey
