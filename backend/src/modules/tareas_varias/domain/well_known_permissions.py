from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission

# Enviar una solicitud de TV propia y ver las propias — del técnico, mismo
# criterio que vacaciones.CREATE (ciclo de vida de las solicitudes propias).
CREATE = Permission(ModuleKey("tareas-varias"), ActionKey("create"))
# Listar pendientes, aprobar/rechazar y cargar una TV a nombre de otro
# técnico — del supervisor, mismo criterio que vacaciones.APPROVE.
APPROVE = Permission(ModuleKey("tareas-varias"), ActionKey("approve"))
