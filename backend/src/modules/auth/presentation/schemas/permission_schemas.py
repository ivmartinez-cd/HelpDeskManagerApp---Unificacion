from pydantic import BaseModel

from src.modules.auth.domain.value_objects.action_key import ActionKey
from src.modules.auth.domain.value_objects.module_key import ModuleKey
from src.modules.auth.domain.value_objects.permission import Permission
from src.modules.auth.domain.value_objects.permission_set import PermissionSet


class PermissionItem(BaseModel):
    module: str
    action: str

    def to_domain(self) -> Permission:
        return Permission(ModuleKey(self.module), ActionKey(self.action))


class PermissionsResponse(BaseModel):
    grants: list[PermissionItem]

    @classmethod
    def from_domain(cls, permissions: PermissionSet) -> "PermissionsResponse":
        items = [
            PermissionItem(module=p.module.value, action=p.action.value)
            for p in permissions.granted
        ]
        return cls(grants=items)


class ReplacePermissionsRequest(BaseModel):
    grants: list[PermissionItem]

    def to_domain(self) -> PermissionSet:
        return PermissionSet(frozenset(item.to_domain() for item in self.grants))
