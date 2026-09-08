from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("bono-tecnicos"), ActionKey("view"))
# Cargar Días es una escritura, no una lectura.
UPDATE = Permission(ModuleKey("bono-tecnicos"), ActionKey("update"))
# Ver "Mi bono" (GET /mi-resumen): puntaje/días/conteos propios del técnico
# autenticado. Hasta el split de Tareas Varias a su propio módulo (ver
# tareas_varias.well_known_permissions) esta acción también habilitaba
# enviar una TV propia; ese uso se fue con el módulo, el nombre de la acción
# ("create") queda por el catálogo compartido de acciones (no es renombrable
# sin migración) pero acá ya solo significa "ver lo propio".
CREATE = Permission(ModuleKey("bono-tecnicos"), ActionKey("create"))
