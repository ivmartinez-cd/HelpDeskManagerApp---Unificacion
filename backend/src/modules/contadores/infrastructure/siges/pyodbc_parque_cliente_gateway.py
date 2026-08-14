"""Adapter pyodbc del puerto ParqueClientePort — catálogo de empresas activas
y conteo de impresoras por cliente contra Siges/MERCURIO. La plomería pyodbc
vive en el `MercurioQueryRunner` compartido (ADR-018)."""

from src.modules.contadores.domain.ports.parque_cliente_port import (
    EmpresaConParque,
    EmpresaSiges,
)
from src.modules.contadores.infrastructure.siges.query import (
    EMPRESAS_ACTIVAS_SQL,
    EMPRESAS_BUSCAR_SQL,
    build_impresoras_por_empresa_sql,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcParqueClienteGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def list_empresas_activas(self) -> list[EmpresaSiges]:
        rows = await self._runner.fetch_all(
            EMPRESAS_ACTIVAS_SQL,
            gateway="parque_cliente",
            log_message="Fallo el catálogo de empresas activas contra Siges/MERCURIO",
        )
        return [
            EmpresaSiges(id=int(row.ID_Empresa), den_comercial=str(row.Den_Comercial).strip())
            for row in rows
        ]

    async def count_impresoras_by_empresa_ids(self, empresa_ids: list[int]) -> dict[int, int]:
        if not empresa_ids:
            return {}
        rows = await self._runner.fetch_all(
            build_impresoras_por_empresa_sql(len(empresa_ids)),
            empresa_ids,
            gateway="parque_cliente",
            log_message="Fallo el conteo de impresoras por cliente contra Siges/MERCURIO",
            log_extra={"cantidad_empresas": len(empresa_ids)},
        )
        return {int(row.ID_Empresa): int(row.impresoras) for row in rows}

    async def search_empresas_activas(self, texto: str) -> list[EmpresaConParque]:
        if not texto.strip():
            return []
        rows = await self._runner.fetch_all(
            EMPRESAS_BUSCAR_SQL,
            [f"%{texto.strip()}%"],
            gateway="parque_cliente",
            log_message="Fallo la búsqueda de empresas contra Siges/MERCURIO",
            log_extra={"texto": texto},
        )
        return [
            EmpresaConParque(
                id=int(row.ID_Empresa),
                den_comercial=str(row.Den_Comercial).strip(),
                impresoras=int(row.impresoras),
            )
            for row in rows
        ]
