import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TecnicoVinculado:
    id_tecnico: int
    tecnico: str


class TecnicoIdentityGateway(Protocol):
    """Resuelve qué técnico de Siges es el usuario autenticado — cruza con el
    vínculo Empleado↔Siges de Gestión de Personal (`vacaciones.Empleado.
    user_id`/`siges_empresa_id`, ver `dias_sugeridos_gateway` para el mismo
    cruce ya usado en este módulo). `None` si el usuario no tiene un
    `Empleado` vinculado, o el `Empleado` no tiene `siges_empresa_id` cargado."""

    async def get_por_usuario(self, user_id: uuid.UUID) -> TecnicoVinculado | None: ...
