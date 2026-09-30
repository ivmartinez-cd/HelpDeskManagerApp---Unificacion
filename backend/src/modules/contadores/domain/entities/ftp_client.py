import uuid
from dataclasses import dataclass

DEFAULT_PATH = "/"
DEFAULT_PATTERN = "PrinterMonitorClient.db3.*"


@dataclass(slots=True, eq=False)
class FtpClient:
    """Config de acceso al servidor FTP de un cliente para bajar sus DB3 de
    contadores. Con `grupo_economico_id`, usuario y contraseña se leen de Siges al
    procesar y `password` queda en None; sin vínculo (clientes pendientes de
    revisar), se usa la contraseña local, en texto plano como en la app vieja."""

    id: uuid.UUID
    name: str
    host: str
    user: str
    password: str | None
    path: str = DEFAULT_PATH
    pattern: str = DEFAULT_PATTERN
    grupo_economico_id: int | None = None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FtpClient) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
