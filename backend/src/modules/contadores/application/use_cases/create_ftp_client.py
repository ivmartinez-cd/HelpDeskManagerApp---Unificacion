import uuid

from src.modules.contadores.application.dtos.ftp_client_dto import FtpClientRequest, FtpClientResult
from src.modules.contadores.application.use_cases._ftp_client_mapper import to_ftp_client_result
from src.modules.contadores.domain.entities.ftp_client import FtpClient
from src.modules.contadores.domain.errors import DuplicateFtpClientNameError
from src.modules.contadores.domain.repositories.ftp_client_repository import FtpClientRepository


class CreateFtpClientUseCase:
    """Crea un nuevo cliente FTP.

    Lanza DuplicateFtpClientNameError si ya existe un cliente con el mismo nombre.
    """

    def __init__(self, repo: FtpClientRepository) -> None:
        self._repo = repo

    async def execute(self, request: FtpClientRequest) -> FtpClientResult:
        existing = await self._repo.get_by_name(request.name)
        if existing is not None:
            raise DuplicateFtpClientNameError(request.name)

        # El router ya valida que password no sea None antes de crear el
        # use case (ver ftp_clients_router.create_ftp_client) — acá solo lo
        # confirmamos para el type checker.
        assert request.password is not None
        client = FtpClient(
            id=uuid.uuid4(),
            name=request.name,
            host=request.host,
            user=request.user,
            password=request.password,
            path=request.path,
            pattern=request.pattern,
        )
        await self._repo.add(client)
        return to_ftp_client_result(client)
