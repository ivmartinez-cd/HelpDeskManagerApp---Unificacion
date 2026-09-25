from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("reporte-incidentes"), ActionKey("view"))
# Corregir la tipificación de un incidente, disparar la tipificación con IA
# (cuesta dinero) y editar la taxonomía.
UPDATE = Permission(ModuleKey("reporte-incidentes"), ActionKey("update"))
