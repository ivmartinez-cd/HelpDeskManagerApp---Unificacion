"""Adapter pyodbc del puerto OperadorCatalogPort — resuelve identidad real
(nombre/apellido/color) de operadores de Gestión contra `dbo.UsuariosWeb` en
Siges/MERCURIO (ver ADR-012). La plomería pyodbc vive en el
`MercurioQueryRunner` compartido (ADR-018)."""

from typing import Any

from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.infrastructure.siges.query import build_usuarios_web_por_logins_sql
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcOperadorGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def find_by_logins(self, logins: list[str]) -> list[Operador]:
        if not logins:
            return []
        rows = await self._runner.fetch_all(
            build_usuarios_web_por_logins_sql(len(logins)),
            logins,
            gateway="operadores",
            log_message="Fallo la consulta de operadores contra Siges/MERCURIO",
            log_extra={"cantidad_logins": len(logins)},
        )
        return [_to_operador(row) for row in rows]


def _to_operador(row: Any) -> Operador:
    nombre = f"{row.nombre or ''} {row.apellido or ''}".strip() or str(row.login)
    return Operador(id=str(row.login), nombre=nombre, color=row.color)
