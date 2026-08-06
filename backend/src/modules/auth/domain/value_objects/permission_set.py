from dataclasses import dataclass

from src.modules.auth.domain.value_objects.module_key import ModuleKey
from src.modules.auth.domain.value_objects.permission import Permission


@dataclass(frozen=True, slots=True)
class PermissionSet:
    """Los permisos concedidos a un usuario. Ausencia de fila = denegado:

    `allows` nunca lanza para un módulo/acción desconocido, simplemente
    devuelve False (fail-closed por construcción, ver ADR-005).
    """

    granted: frozenset[Permission]

    def allows(self, permission: Permission) -> bool:
        return permission in self.granted

    def modules(self) -> frozenset[ModuleKey]:
        return frozenset(p.module for p in self.granted)
