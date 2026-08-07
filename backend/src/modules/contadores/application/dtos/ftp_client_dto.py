from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FtpClientRequest:
    """Input común para crear o actualizar un cliente FTP."""

    name: str
    host: str
    user: str
    password: str
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
