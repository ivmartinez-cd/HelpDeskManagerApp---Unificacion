from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FtpClientRequest:
    """Input común para crear o actualizar un cliente FTP. `password=None`
    solo es válido para update (CreateFtpClientUseCase exige que no sea
    None; el router ya lo valida antes de llegar acá, ver ftp_clients_router).
    """

    name: str
    host: str
    user: str
    password: str | None
    path: str = "/"
    pattern: str = "PrinterMonitorClient.db3.*"


@dataclass(frozen=True, slots=True)
class FtpClientResult:
    """Output de un cliente FTP (nunca expone el password)."""

    id: str
    name: str
    host: str
    user: str
    path: str
    pattern: str
