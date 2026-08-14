"""Consulta read-only contra `dbo.UsuariosWeb` de Siges — misma cuenta
`db_datareader` (`SLA_MERCURIO_USER`) que ya usa `sla`/`prestadores`, sin
permisos de escritura (verificado con `IS_ROLEMEMBER`/`fn_my_permissions`,
ver ADR-012). No hay forma verificada de filtrar solo "operadores de
facturación" en `UsuariosWeb` — la tabla tiene empleados de todo tipo — así
que se resuelve por `login` puntual, no se enumera el catálogo completo.
Filtrada con placeholders pyodbc, no se interpola nada (ARCHITECTURE_GUIDE
§8)."""

USUARIOS_WEB_POR_LOGINS_SQL = """
SELECT login, nombre, apellido, color
FROM dbo.UsuariosWeb
WHERE login IN ({placeholders})
"""

# Catálogo de empresas activas para el cruce por nombre del cliente de los
# eventos (ver cliente_matcher). `Estado=0` es activo — la convención está
# invertida respecto de la intuición (SIGES_READONLY_CATALOGO_DATOS.md §3).
EMPRESAS_ACTIVAS_SQL = """
SELECT ID_Empresa, Den_Comercial
FROM dbo.Empresa
WHERE Estado = 0
"""

# Impresoras activas por cliente — misma definición de "activa" que el parque
# por PST (paridad verificada contra el reporte legacy, ver
# SIGES_READONLY_CATALOGO_DATOS.md §3), sin el filtro de prestador.
IMPRESORAS_POR_EMPRESA_SQL = """
SELECT M.ID_Empresa, COUNT(*) AS impresoras
FROM dbo.Maquina M
WHERE M.ID_Empresa IN ({placeholders})
  AND M.Estado = 0
  AND M.ID_Estado_Maquina NOT IN (2, 8)
GROUP BY M.ID_Empresa
"""

# Búsqueda para resolver clientes sin cruce: empresas activas por LIKE con su
# parque a la vista. El patrón (%texto%) se arma en el gateway pero viaja como
# parámetro, nunca interpolado (ARCHITECTURE_GUIDE §8). TOP 20: es un combobox
# de búsqueda en vivo, no un listado.
EMPRESAS_BUSCAR_SQL = """
SELECT TOP 20 E.ID_Empresa, E.Den_Comercial,
    (SELECT COUNT(*) FROM dbo.Maquina M
     WHERE M.ID_Empresa = E.ID_Empresa AND M.Estado = 0
       AND M.ID_Estado_Maquina NOT IN (2, 8)) AS impresoras
FROM dbo.Empresa E
WHERE E.Estado = 0 AND E.Den_Comercial LIKE ?
ORDER BY impresoras DESC, E.Den_Comercial
"""


def build_usuarios_web_por_logins_sql(cantidad: int) -> str:
    return USUARIOS_WEB_POR_LOGINS_SQL.format(placeholders=_placeholders(cantidad))


def build_impresoras_por_empresa_sql(cantidad: int) -> str:
    return IMPRESORAS_POR_EMPRESA_SQL.format(placeholders=_placeholders(cantidad))


def _placeholders(cantidad: int) -> str:
    return ", ".join("?" for _ in range(cantidad))
