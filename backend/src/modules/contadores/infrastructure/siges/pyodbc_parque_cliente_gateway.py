"""Adapter pyodbc del puerto ParqueClientePort — catálogo de empresas activas
y conteo de impresoras por cliente contra Siges/MERCURIO. Mismo criterio que
PyodbcOperadorGateway: pyodbc es síncrono, la consulta corre en un thread;
conexión nueva por consulta (fetch esporádico de card de Inicio, no hot
path)."""

import asyncio
import logging
from collections.abc import Sequence
from typing import Any

import pyodbc

from src.modules.contadores.domain.ports.parque_cliente_port import (
    EmpresaConParque,
    EmpresaSiges,
)
from src.modules.contadores.infrastructure.siges.query import (
    EMPRESAS_ACTIVAS_SQL,
    EMPRESAS_BUSCAR_SQL,
    build_impresoras_por_empresa_sql,
)
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class PyodbcParqueClienteGateway:
    def __init__(self, connection_string: str, timeout_seconds: float) -> None:
        self._connection_string = connection_string
        self._timeout_seconds = timeout_seconds

    async def list_empresas_activas(self) -> list[EmpresaSiges]:
        try:
            rows = await asyncio.to_thread(self._fetch, EMPRESAS_ACTIVAS_SQL, [])
        except pyodbc.Error as exc:
            logger.error(
                "Fallo el catálogo de empresas activas contra Siges/MERCURIO", exc_info=exc
            )
            raise ExternalServiceError(
                "No se pudo consultar la base Siges (MERCURIO)"
            ) from exc
        return [
            EmpresaSiges(id=int(row.ID_Empresa), den_comercial=str(row.Den_Comercial).strip())
            for row in rows
        ]

    async def count_impresoras_by_empresa_ids(self, empresa_ids: list[int]) -> dict[int, int]:
        if not empresa_ids:
            return {}
        sql = build_impresoras_por_empresa_sql(len(empresa_ids))
        try:
            rows = await asyncio.to_thread(self._fetch, sql, empresa_ids)
        except pyodbc.Error as exc:
            logger.error(
                "Fallo el conteo de impresoras por cliente contra Siges/MERCURIO",
                extra={"cantidad_empresas": len(empresa_ids)},
                exc_info=exc,
            )
            raise ExternalServiceError(
                "No se pudo consultar la base Siges (MERCURIO)"
            ) from exc
        return {int(row.ID_Empresa): int(row.impresoras) for row in rows}

    async def search_empresas_activas(self, texto: str) -> list[EmpresaConParque]:
        if not texto.strip():
            return []
        try:
            rows = await asyncio.to_thread(
                self._fetch, EMPRESAS_BUSCAR_SQL, [f"%{texto.strip()}%"]
            )
        except pyodbc.Error as exc:
            logger.error(
                "Fallo la búsqueda de empresas contra Siges/MERCURIO",
                extra={"texto": texto},
                exc_info=exc,
            )
            raise ExternalServiceError(
                "No se pudo consultar la base Siges (MERCURIO)"
            ) from exc
        return [
            EmpresaConParque(
                id=int(row.ID_Empresa),
                den_comercial=str(row.Den_Comercial).strip(),
                impresoras=int(row.impresoras),
            )
            for row in rows
        ]

    def _fetch(self, sql: str, params: Sequence[int | str]) -> list[Any]:
        with pyodbc.connect(
            self._connection_string, timeout=int(self._timeout_seconds)
        ) as connection:
            connection.timeout = int(self._timeout_seconds)
            cursor = connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return list(cursor.fetchall())
