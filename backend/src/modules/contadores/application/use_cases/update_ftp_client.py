import uuid

from src.modules.contadores.application.dtos.ftp_client_dto import FtpClientRequest, FtpClientResult
from src.modules.contadores.application.use_cases._ftp_client_mapper import to_ftp_client_result
from src.modules.contadores.domain.errors import FtpClientNotFoundError
from src.modules.contadores.domain.repositories.ftp_client_repository import FtpClientRepository


class UpdateFtpClientUseCase:
    """Actualiza los datos de un cliente FTP existente.

    Lanza FtpClientNotFoundError si el ID no corresponde a ningún cliente.
    """

    def __init__(self, repo: FtpClientRepository) -> None:
        self._repo = repo

    async def execute(self, client_id: uuid.UUID, request: FtpClientRequest) -> FtpClientResult:
        client = await self._repo.get_by_id(client_id)
        if client is None:
            raise FtpClientNotFoundError()

        client.name = request.name
        client.host = request.host
        client.user = request.user
        if request.password:
            client.password = request.password
        client.path = request.path
        client.pattern = request.pattern

        await self._repo.save(client)
        return to_ftp_client_result(client)
