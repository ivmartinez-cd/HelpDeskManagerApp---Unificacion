from src.modules.contadores.application.dtos.ftp_client_dto import FtpClientResult
from src.modules.contadores.application.use_cases._ftp_client_mapper import (
    to_ftp_client_result,
)
from src.modules.contadores.domain.repositories.ftp_client_repository import FtpClientRepository


class ListFtpClientsUseCase:
    """Devuelve todos los clientes FTP ordenados por nombre."""

    def __init__(self, repo: FtpClientRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[FtpClientResult]:
        clients = await self._repo.list_all()
        return [to_ftp_client_result(c) for c in clients]
