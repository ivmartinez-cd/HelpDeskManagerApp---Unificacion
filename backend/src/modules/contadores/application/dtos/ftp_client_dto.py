from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FtpClientRequest:
    """Input para crear o actualizar un cliente FTP. Servidor, usuario y contraseña
    no se cargan a mano: salen del grupo económico de Siges. `grupo_economico_id`
    es obligatorio al crear; al editar, None conserva el vínculo actual."""

    name: str
    grupo_economico_id: int | None
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
    grupo_economico_id: int | None
