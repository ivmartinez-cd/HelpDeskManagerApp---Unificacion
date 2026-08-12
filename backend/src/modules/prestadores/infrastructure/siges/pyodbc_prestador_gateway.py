"""Adapter pyodbc del puerto SigesPrestadorGateway — mismo criterio que
`PyodbcSlaQueryGateway`: pyodbc es síncrono, la consulta corre en un thread;
conexión nueva por consulta (fetch esporádico, no hot path)."""

import asyncio
import logging
from typing import Any

import pyodbc

from src.modules.prestadores.domain.repositories.siges_prestador_gateway import (
    SigesPrestadorInfo,
)
from src.modules.prestadores.infrastructure.siges.query import build_empresa_por_ids_sql
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


def _texto(value: Any) -> str | None:
    if value is None:
        return None
    texto = str(value).strip()
    return texto or None


class PyodbcPrestadorGateway:
    def __init__(self, connection_string: str, timeout_seconds: float) -> None:
        self._connection_string = connection_string
        self._timeout_seconds = timeout_seconds

    async def find_by_siges_ids(self, siges_empresa_ids: list[int]) -> list[SigesPrestadorInfo]:
        if not siges_empresa_ids:
            return []
        try:
            rows = await asyncio.to_thread(self._query, siges_empresa_ids)
        except pyodbc.Error as exc:
            logger.error(
                "Fallo la consulta de prestadores contra Siges/MERCURIO",
                extra={"cantidad_ids": len(siges_empresa_ids)},
                exc_info=exc,
            )
            raise ExternalServiceError(
                "No se pudo consultar la base Siges (MERCURIO)"
            ) from exc
        return [
            SigesPrestadorInfo(
                siges_empresa_id=int(row.ID_Empresa),
                den_comercial=str(row.Den_Comercial).strip(),
                razon_social=_texto(row.razon_social),
                cuit=_texto(row.cuit),
            )
            for row in rows
        ]

    def _query(self, siges_empresa_ids: list[int]) -> list[Any]:
        sql = build_empresa_por_ids_sql(len(siges_empresa_ids))
        with pyodbc.connect(
            self._connection_string, timeout=int(self._timeout_seconds)
        ) as connection:
            connection.timeout = int(self._timeout_seconds)
            cursor = connection.cursor()
            cursor.execute(sql, siges_empresa_ids)
            return list(cursor.fetchall())
