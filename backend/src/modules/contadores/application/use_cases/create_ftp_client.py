import uuid

from src.modules.contadores.application.dtos.ftp_client_dto import FtpClientRequest, FtpClientResult
from src.modules.contadores.application.use_cases._ftp_client_mapper import to_ftp_client_result
from src.modules.contadores.application.use_cases._vinculo_grupo_ftp import usuario_del_grupo
from src.modules.contadores.domain.entities.ftp_client import FtpClient
from src.modules.contadores.domain.errors import DuplicateFtpClientNameError
from src.modules.contadores.domain.repositories.ftp_client_repository import FtpClientRepository
from src.modules.contadores.domain.repositories.grupos_economicos_ftp_gateway import (
    GruposEconomicosFtpGateway,
)


class CreateFtpClientUseCase:
    """Crea un cliente FTP vinculado a un grupo económico de Siges, en el servidor
    FTP de la empresa. Lanza DuplicateFtpClientNameError si el nombre ya existe."""

    def __init__(
        self, repo: FtpClientRepository, grupos: GruposEconomicosFtpGateway, host: str
    ) -> None:
        self._repo = repo
        self._grupos = grupos
        self._host = host

    async def execute(self, request: FtpClientRequest) -> FtpClientResult:
        if await self._repo.get_by_name(request.name) is not None:
            raise DuplicateFtpClientNameError(request.name)
        usuario = await usuario_del_grupo(self._grupos, request.grupo_economico_id)
        client = FtpClient(
            id=uuid.uuid4(),
            name=request.name,
            host=self._host,
            user=usuario,
            password=None,
            path=request.path,
            pattern=request.pattern,
            grupo_economico_id=request.grupo_economico_id,
        )
        await self._repo.add(client)
        return to_ftp_client_result(client)
