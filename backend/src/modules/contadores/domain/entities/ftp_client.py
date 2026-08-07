import uuid
from dataclasses import dataclass

DEFAULT_PATH = "/"
DEFAULT_PATTERN = "PrinterMonitorClient.db3.*"


@dataclass(slots=True, eq=False)
class FtpClient:
    """Config de acceso al servidor FTP de un cliente para bajar sus DB3 de
    contadores. `password` viaja en texto plano — así vive hoy en la app
    vieja (ver CONTADORES_CARACTERIZACION.md); no se cambia acá sin decisión
    explícita del usuario."""

    id: uuid.UUID
    name: str
    host: str
    user: str
    password: str
    path: str = DEFAULT_PATH
    pattern: str = DEFAULT_PATTERN

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FtpClient) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
