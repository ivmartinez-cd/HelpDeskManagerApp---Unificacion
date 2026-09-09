import uuid

from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoIdentityGateway,
)


class GetVinculoSiges:
    """Si el usuario autenticado tiene vínculo Empleado↔Siges cargado — lo usa
    el frontend para decidir si corresponde mostrar el card "Mi bono"/Tareas
    Varias antes de pedir `/mi-resumen` (que sí tira 404 sin vínculo, ver
    `TecnicoNoVinculadoError`). Sin esto, un superadmin ve todos los módulos
    (`ListVisibleModules`) y disparaba ese 404 aunque no sea técnico."""

    def __init__(self, identity_gateway: TecnicoIdentityGateway) -> None:
        self._identity_gateway = identity_gateway

    async def execute(self, user_id: uuid.UUID) -> bool:
        vinculo = await self._identity_gateway.get_por_usuario(user_id)
        return vinculo is not None
