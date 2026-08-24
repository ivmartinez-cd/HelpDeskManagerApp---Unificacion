from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

VIEW = Permission(ModuleKey("bono-tecnicos"), ActionKey("view"))
# Cargar Días es una escritura, no una lectura.
UPDATE = Permission(ModuleKey("bono-tecnicos"), ActionKey("update"))
# Enviar una solicitud de TV propia (mismo criterio que vacaciones.CREATE:
# ciclo de vida de las solicitudes propias) — del técnico, cuando tenga login.
CREATE = Permission(ModuleKey("bono-tecnicos"), ActionKey("create"))
# Listar pendientes y aprobar/rechazar solicitudes de TV ajenas — del
# supervisor, mismo criterio que vacaciones.APPROVE.
APPROVE = Permission(ModuleKey("bono-tecnicos"), ActionKey("approve"))
