import uuid
from typing import Protocol

from src.modules.auth.domain.value_objects.department_scope import DepartmentScope
from src.modules.auth.domain.value_objects.module_key import ModuleKey


class ScopePolicy(Protocol):
    """Alcance sectorial PREVISTO, sin lógica todavía — ver user_module_scope.
    Única implementación en esta fase: GlobalScopePolicy (Etapa 6)."""

    def scope_for(self, *, user_id: uuid.UUID, module: ModuleKey) -> DepartmentScope: ...
