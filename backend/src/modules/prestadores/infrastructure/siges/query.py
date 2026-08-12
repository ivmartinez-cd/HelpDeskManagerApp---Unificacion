"""Consulta read-only contra `dbo.Empresa` de Siges — la misma tabla y la
misma cuenta `db_datareader` (`SLA_MERCURIO_USER`) que ya usa el módulo sla,
sin permisos de escritura (verificado: INSERT/UPDATE/DELETE/ALTER dan 0 vía
`HAS_PERMS_BY_NAME`). Filtrada por `ID_Empresa` con placeholders pyodbc, no
se interpola nada (ARCHITECTURE_GUIDE §8)."""

EMPRESA_POR_IDS_SQL = """
SELECT ID_Empresa, Den_Comercial, razon_social, cuit
FROM dbo.Empresa
WHERE ID_Empresa IN ({placeholders})
"""


def build_empresa_por_ids_sql(cantidad: int) -> str:
    placeholders = ", ".join("?" for _ in range(cantidad))
    return EMPRESA_POR_IDS_SQL.format(placeholders=placeholders)
