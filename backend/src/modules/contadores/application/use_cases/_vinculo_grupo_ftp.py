from dataclasses import replace

from src.modules.contadores.domain.entities.ftp_client import FtpClient
from src.modules.contadores.domain.errors import (
    FtpGrupoEconomicoRequeridoError,
    GrupoEconomicoSinFtpError,
)
from src.modules.contadores.domain.repositories.grupos_economicos_ftp_gateway import (
    GruposEconomicosFtpGateway,
)


async def usuario_del_grupo(grupos: GruposEconomicosFtpGateway, grupo_id: int | None) -> str:
    if grupo_id is None:
        raise FtpGrupoEconomicoRequeridoError()
    credenciales = await grupos.credenciales(grupo_id)
    if credenciales is None:
        raise GrupoEconomicoSinFtpError(grupo_id)
    return credenciales.usuario


async def con_credenciales_de_siges(
    client: FtpClient, grupos: GruposEconomicosFtpGateway
) -> FtpClient:
    """El cliente listo para conectarse: vinculado, con usuario y contraseña de
    Siges; sin vínculo (pendiente de revisar), con los locales."""
    if client.grupo_economico_id is None:
        return client
    credenciales = await grupos.credenciales(client.grupo_economico_id)
    if credenciales is None:
        raise GrupoEconomicoSinFtpError(client.grupo_economico_id)
    return replace(client, user=credenciales.usuario, password=credenciales.password)
