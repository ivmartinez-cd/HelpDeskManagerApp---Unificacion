import uuid

from src.modules.contadores.domain.errors import FtpClientNotFoundError
from src.modules.contadores.domain.repositories.ftp_client_repository import FtpClientRepository


class DeleteFtpClientUseCase:
    """Elimina un cliente FTP por ID.

    Lanza FtpClientNotFoundError si el ID no corresponde a ningún cliente.
    """

    def __init__(self, repo: FtpClientRepository) -> None:
        self._repo = repo

    async def execute(self, client_id: uuid.UUID) -> None:
        client = await self._repo.get_by_id(client_id)
        if client is None:
            raise FtpClientNotFoundError()
        await self._repo.delete(client_id)
