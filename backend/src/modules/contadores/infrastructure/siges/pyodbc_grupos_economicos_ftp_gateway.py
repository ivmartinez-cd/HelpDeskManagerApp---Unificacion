"""Usuario y contraseña FTP de `dbo.GrupoEconomico` en Siges/ORION. La contraseña
solo se lee al procesar un cliente, nunca en el listado."""

from src.modules.contadores.domain.repositories.grupos_economicos_ftp_gateway import (
    CredencialesFtp,
    GrupoEconomicoFtp,
)
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner

_SQL_LISTAR = """
SELECT id, descripcion, LTRIM(RTRIM(userftp)) AS usuario
FROM dbo.GrupoEconomico
WHERE ISNULL(LTRIM(RTRIM(userftp)), '') <> '' AND ISNULL(passftp, '') <> ''
ORDER BY descripcion
"""

_SQL_CREDENCIALES = """
SELECT LTRIM(RTRIM(userftp)) AS usuario, passftp AS password
FROM dbo.GrupoEconomico
WHERE id = ? AND ISNULL(LTRIM(RTRIM(userftp)), '') <> '' AND ISNULL(passftp, '') <> ''
"""


class PyodbcGruposEconomicosFtpGateway:
    def __init__(self, runner: OrionQueryRunner) -> None:
        self._runner = runner

    async def listar(self) -> list[GrupoEconomicoFtp]:
        rows = await self._runner.fetch_all(
            _SQL_LISTAR,
            gateway="grupos_economicos_ftp",
            log_message="Falló el listado de grupos económicos con FTP contra Siges/ORION",
        )
        return [GrupoEconomicoFtp(int(r.id), str(r.descripcion).strip(), r.usuario) for r in rows]

    async def credenciales(self, grupo_id: int) -> CredencialesFtp | None:
        rows = await self._runner.fetch_all(
            _SQL_CREDENCIALES,
            (grupo_id,),
            gateway="grupos_economicos_ftp",
            log_message="Falló la lectura de credenciales FTP contra Siges/ORION",
            log_extra={"grupo_economico_id": grupo_id},
        )
        return CredencialesFtp(rows[0].usuario, rows[0].password) if rows else None
