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

# Parque de equipos activos por PST — misma definición que el reporte legacy
# "Maquinas Activas por Prestador" (sitesphp), paridad exacta verificada
# 2026-08-14 contra PST Villa Mercedes (841/841). La baja tiene doble condición
# a propósito: hay máquinas 'De Baja' (ID_Estado_Maquina=2) que siguen con
# Maquina.Estado=0 — hacen falta los dos filtros. Detalle en
# docs/siges/SIGES_READONLY_CATALOGO_DATOS.md §3.
EQUIPOS_POR_PRESTADOR_SQL = """
SELECT S.ID_Prestador, COUNT(*) AS equipos
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
WHERE S.ID_Prestador IN ({placeholders})
  AND S.Estado = 0
  AND M.Estado = 0
  AND M.ID_Estado_Maquina NOT IN (2, 8)
GROUP BY S.ID_Prestador
"""


def build_empresa_por_ids_sql(cantidad: int) -> str:
    return EMPRESA_POR_IDS_SQL.format(placeholders=_placeholders(cantidad))


def build_equipos_por_prestador_sql(cantidad: int) -> str:
    return EQUIPOS_POR_PRESTADOR_SQL.format(placeholders=_placeholders(cantidad))


def _placeholders(cantidad: int) -> str:
    return ", ".join("?" for _ in range(cantidad))
