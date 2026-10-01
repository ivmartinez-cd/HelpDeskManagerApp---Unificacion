import uuid

from src.modules.tareas_varias.domain.errors import AutoaprobacionTvError
from src.modules.tareas_varias.domain.repositories.tecnico_identity_gateway import (
    TecnicoIdentityGateway,
)


async def verificar_no_es_propia(
    identidades: TecnicoIdentityGateway, user_id: uuid.UUID, id_tecnico: int
) -> None:
    vinculo = await identidades.get_por_usuario(user_id)
    if vinculo is not None and vinculo.id_tecnico == id_tecnico:
        raise AutoaprobacionTvError()
