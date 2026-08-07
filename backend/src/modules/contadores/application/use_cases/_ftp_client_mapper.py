"""Helpers internos de application/use_cases para evitar duplicar _to_result."""
from src.modules.contadores.application.dtos.ftp_client_dto import FtpClientResult
from src.modules.contadores.domain.entities.ftp_client import FtpClient


def to_ftp_client_result(client: FtpClient) -> FtpClientResult:
    return FtpClientResult(
        id=str(client.id),
        name=client.name,
        host=client.host,
        user=client.user,
        path=client.path,
        pattern=client.pattern,
    )
