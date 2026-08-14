"""Adapter pyodbc del puerto SigesPrestadorGateway. La plomería pyodbc vive en
el `MercurioQueryRunner` compartido (ADR-018); acá quedan el SQL y el mapeo de
filas propios de prestadores."""

from typing import Any

from src.modules.prestadores.domain.repositories.siges_prestador_gateway import (
    SigesPrestadorInfo,
)
from src.modules.prestadores.infrastructure.siges.query import (
    build_empresa_por_ids_sql,
    build_equipos_por_prestador_sql,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


def _texto(value: Any) -> str | None:
    if value is None:
        return None
    texto = str(value).strip()
    return texto or None


class PyodbcPrestadorGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def find_by_siges_ids(self, siges_empresa_ids: list[int]) -> list[SigesPrestadorInfo]:
        if not siges_empresa_ids:
            return []
        rows = await self._runner.fetch_all(
            build_empresa_por_ids_sql(len(siges_empresa_ids)),
            siges_empresa_ids,
            gateway="prestadores",
            log_message="Fallo la consulta de prestadores contra Siges/MERCURIO",
            log_extra={"cantidad_ids": len(siges_empresa_ids)},
        )
        return [
            SigesPrestadorInfo(
                siges_empresa_id=int(row.ID_Empresa),
                den_comercial=str(row.Den_Comercial).strip(),
                razon_social=_texto(row.razon_social),
                cuit=_texto(row.cuit),
            )
            for row in rows
        ]

    async def count_equipos_by_siges_ids(self, siges_empresa_ids: list[int]) -> dict[int, int]:
        if not siges_empresa_ids:
            return {}
        rows = await self._runner.fetch_all(
            build_equipos_por_prestador_sql(len(siges_empresa_ids)),
            siges_empresa_ids,
            gateway="prestadores",
            log_message="Fallo el conteo de equipos por PST contra Siges/MERCURIO",
            log_extra={"cantidad_ids": len(siges_empresa_ids)},
        )
        return {int(row.ID_Prestador): int(row.equipos) for row in rows}
