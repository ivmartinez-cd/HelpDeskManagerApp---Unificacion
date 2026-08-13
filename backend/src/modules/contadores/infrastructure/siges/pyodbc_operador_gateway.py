"""Adapter pyodbc del puerto OperadorCatalogPort — resuelve identidad real
(nombre/apellido/color) de operadores de Gestión contra `dbo.UsuariosWeb` en
Siges/MERCURIO (ver ADR-012). Mismo criterio que PyodbcSlaQueryGateway:
pyodbc es síncrono, la consulta corre en un thread; conexión nueva por
consulta (fetch esporádico, no hot path)."""

import asyncio
import logging
from typing import Any

import pyodbc

from src.modules.contadores.domain.entities.operador import Operador
from src.modules.contadores.infrastructure.siges.query import build_usuarios_web_por_logins_sql
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class PyodbcOperadorGateway:
    def __init__(self, connection_string: str, timeout_seconds: float) -> None:
        self._connection_string = connection_string
        self._timeout_seconds = timeout_seconds

    async def find_by_logins(self, logins: list[str]) -> list[Operador]:
        if not logins:
            return []
        try:
            rows = await asyncio.to_thread(self._query, logins)
        except pyodbc.Error as exc:
            logger.error(
                "Fallo la consulta de operadores contra Siges/MERCURIO",
                extra={"cantidad_logins": len(logins)},
                exc_info=exc,
            )
            raise ExternalServiceError(
                "No se pudo consultar la base Siges (MERCURIO)"
            ) from exc
        return [_to_operador(row) for row in rows]

    def _query(self, logins: list[str]) -> list[Any]:
        sql = build_usuarios_web_por_logins_sql(len(logins))
        with pyodbc.connect(
            self._connection_string, timeout=int(self._timeout_seconds)
        ) as connection:
            connection.timeout = int(self._timeout_seconds)
            cursor = connection.cursor()
            cursor.execute(sql, logins)
            return list(cursor.fetchall())


def _to_operador(row: Any) -> Operador:
    nombre = f"{row.nombre or ''} {row.apellido or ''}".strip() or str(row.login)
    return Operador(id=str(row.login), nombre=nombre, color=row.color)
