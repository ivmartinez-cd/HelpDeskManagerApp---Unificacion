from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GrupoEconomicoFtp:
    """Grupo económico de Siges con usuario FTP cargado (sin la contraseña)."""

    id: int
    descripcion: str
    usuario: str


@dataclass(frozen=True, slots=True)
class CredencialesFtp:
    usuario: str
    password: str


class GruposEconomicosFtpGateway(Protocol):
    """Usuario y contraseña FTP de los clientes, tal como los carga Siges."""

    async def listar(self) -> list[GrupoEconomicoFtp]: ...

    async def credenciales(self, grupo_id: int) -> CredencialesFtp | None:
        """None si el grupo no existe o no tiene usuario/contraseña FTP."""
        ...
