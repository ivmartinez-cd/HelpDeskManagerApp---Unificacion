from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

_MODULE = ModuleKey("analisis-log-hp")

VIEW = Permission(_MODULE, ActionKey("view"))
# Toda mutación (guardar/editar/borrar análisis, catalogar códigos de error, subir
# manuales CPMD) — mismo criterio que turnos.MANAGE (ADR-029): un solo bucket de
# escritura, sin distinción create/update/delete que el módulo no necesita.
MANAGE = Permission(_MODULE, ActionKey("manage"))
