from dataclasses import dataclass

from src.modules.auth.domain.value_objects.action_key import ActionKey
from src.modules.auth.domain.value_objects.module_key import ModuleKey


@dataclass(frozen=True, slots=True)
class ModuleCatalogEntry:
    key: ModuleKey
    label: str
    route: str
    icon: str
    sort_order: int
    is_enabled: bool
    # Qué acciones son válidas para este módulo (module_action) — la grilla
    # de permisos (Etapa 13) solo puede ofrecer estos pares, los demás
    # fallarían con la FK compuesta de permission_grant (ver ADR-005).
    actions: frozenset[ActionKey]
