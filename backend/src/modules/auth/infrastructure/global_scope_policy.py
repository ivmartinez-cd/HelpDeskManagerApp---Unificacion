import uuid

from src.modules.auth.domain.value_objects.department_scope import DepartmentScope, GlobalScope
from src.shared.domain.value_objects.module_key import ModuleKey


class GlobalScopePolicy:
    """Única implementación del puerto ScopePolicy en esta fase: todo usuario
    ve el módulo completo, sin restricción de sector (ver user_module_scope,
    previsto en el schema pero sin lógica hasta migrar vacaciones)."""

    def scope_for(self, *, user_id: uuid.UUID, module: ModuleKey) -> DepartmentScope:
        return GlobalScope()
