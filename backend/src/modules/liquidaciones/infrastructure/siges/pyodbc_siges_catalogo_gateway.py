"""Adapter pyodbc del puerto SigesCatalogoGateway — mismo criterio que
`PyodbcPrestadorGateway` del módulo prestadores: pyodbc es síncrono, la consulta
corre en un thread; conexión nueva por consulta (fetch esporádico, no hot path)."""

import asyncio
import logging
from typing import Any

import pyodbc

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesEmpresaInfo,
    TipoEmpresaSiges,
)
from src.modules.liquidaciones.infrastructure.siges.query import EMPRESAS_PST_ACTIVAS_SQL
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


def _texto(value: Any) -> str | None:
    if value is None:
        return None
    texto = str(value).strip()
    return texto or None


def _tipo(den_comercial: str) -> TipoEmpresaSiges:
    return "SPST" if den_comercial.upper().startswith("SPST") else "PST"


class PyodbcSigesCatalogoGateway:
    def __init__(self, connection_string: str, timeout_seconds: float) -> None:
        self._connection_string = connection_string
        self._timeout_seconds = timeout_seconds

    async def list_empresas_activas(self) -> list[SigesEmpresaInfo]:
        try:
            rows = await asyncio.to_thread(self._query)
        except pyodbc.Error as exc:
            logger.error(
                "Fallo la consulta del catálogo PST/SPST contra Siges/MERCURIO",
                exc_info=exc,
            )
            raise ExternalServiceError("No se pudo consultar la base Siges (MERCURIO)") from exc
        return [
            SigesEmpresaInfo(
                siges_empresa_id=int(row.ID_Empresa),
                den_comercial=str(row.Den_Comercial).strip(),
                razon_social=_texto(row.razon_social),
                cuit=_texto(row.cuit),
                tipo=_tipo(str(row.Den_Comercial).strip()),
            )
            for row in rows
        ]

    def _query(self) -> list[Any]:
        with pyodbc.connect(
            self._connection_string, timeout=int(self._timeout_seconds)
        ) as connection:
            connection.timeout = int(self._timeout_seconds)
            cursor = connection.cursor()
            cursor.execute(EMPRESAS_PST_ACTIVAS_SQL)
            return list(cursor.fetchall())
