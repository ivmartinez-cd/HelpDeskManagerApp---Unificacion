import uuid

from src.modules.contadores.application.dtos.ftp_client_dto import FtpClientRequest, FtpClientResult
from src.modules.contadores.application.use_cases._ftp_client_mapper import to_ftp_client_result
from src.modules.contadores.application.use_cases._vinculo_grupo_ftp import usuario_del_grupo
from src.modules.contadores.domain.errors import FtpClientNotFoundError
from src.modules.contadores.domain.repositories.ftp_client_repository import FtpClientRepository
from src.modules.contadores.domain.repositories.grupos_economicos_ftp_gateway import (
    GruposEconomicosFtpGateway,
)


class UpdateFtpClientUseCase:
    """Edita nombre, carpeta y patrón; servidor, usuario y contraseña no se tocan a
    mano. Vincular un grupo económico pasa a leer las credenciales de Siges y
    descarta la contraseña local. Lanza FtpClientNotFoundError si el ID no existe."""

    def __init__(self, repo: FtpClientRepository, grupos: GruposEconomicosFtpGateway) -> None:
        self._repo = repo
        self._grupos = grupos

    async def execute(self, client_id: uuid.UUID, request: FtpClientRequest) -> FtpClientResult:
        client = await self._repo.get_by_id(client_id)
        if client is None:
            raise FtpClientNotFoundError()
        grupo_id = request.grupo_economico_id
        if grupo_id is not None and grupo_id != client.grupo_economico_id:
            client.user = await usuario_del_grupo(self._grupos, grupo_id)
            client.password = None
            client.grupo_economico_id = grupo_id
        client.name = request.name
        client.path = request.path
        client.pattern = request.pattern
        await self._repo.save(client)
        return to_ftp_client_result(client)
