from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("bono-tecnicos"), ActionKey("view"))
# Cargar Días/Tareas Varias es una escritura, no una lectura.
UPDATE = Permission(ModuleKey("bono-tecnicos"), ActionKey("update"))
