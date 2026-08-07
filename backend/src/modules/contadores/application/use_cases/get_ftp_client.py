import uuid

from src.modules.contadores.application.dtos.ftp_client_dto import FtpClientResult
from src.modules.contadores.application.use_cases._ftp_client_mapper import to_ftp_client_result
from src.modules.contadores.domain.errors import FtpClientNotFoundError
from src.modules.contadores.domain.repositories.ftp_client_repository import FtpClientRepository


class GetFtpClientUseCase:
    """Devuelve un cliente FTP por ID o lanza FtpClientNotFoundError."""

    def __init__(self, repo: FtpClientRepository) -> None:
        self._repo = repo

    async def execute(self, client_id: uuid.UUID) -> FtpClientResult:
        client = await self._repo.get_by_id(client_id)
        if client is None:
            raise FtpClientNotFoundError()
        return to_ftp_client_result(client)
