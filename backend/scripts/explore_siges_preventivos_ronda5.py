"""Ronda 5 de exploración de preventivos: el usuario reporta que la pantalla
trae (a) clientes dados de baja y (b) la empresa propia CD1. Hipótesis: la
consulta filtra máquina/sucursal activas pero no `Empresa.Estado`, ni excluye
empresas internas de Canal Directo. Se mide cuánto pesa cada caso en el
universo actual y se busca un criterio de datos para "empresa interna"
(¿ID_Tipo_Empresa? ¿prefijo de Den_Comercial?). Solo SELECTs.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_ronda5.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

# Universo actual de la pantalla (todas las zonas locales juntas, aprox:
# excluye INTERIOR y agrupaciones), agrupado por estado de la empresa.
_SQL_POR_ESTADO_EMPRESA = """
SELECT E.Estado AS estado_empresa, COUNT(*) AS maquinas,
       COUNT(DISTINCT E.ID_Empresa) AS empresas
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
  AND S.Cuadricula IN ('SUR','SUROESTE','SUORESTE','OESTE','CENTRO','SMARTIN',
                       'CABA','CABA-N','CABA-S','CABA-O',
                       'NORTE1','NORTE2','NORTE3','NORTE4')
GROUP BY E.Estado
"""

# Clientes dados de baja (Estado=1) que hoy aparecen: top por máquinas.
_SQL_CLIENTES_DE_BAJA = """
SELECT TOP 15 E.ID_Empresa, E.Den_Comercial, E.ID_Tipo_Empresa,
       COUNT(*) AS maquinas
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
  AND S.Cuadricula IN ('SUR','SUROESTE','SUORESTE','OESTE','CENTRO','SMARTIN',
                       'CABA','CABA-N','CABA-S','CABA-O',
                       'NORTE1','NORTE2','NORTE3','NORTE4')
  AND E.Estado = 1
GROUP BY E.ID_Empresa, E.Den_Comercial, E.ID_Tipo_Empresa
ORDER BY maquinas DESC
"""

# Empresas internas de CD que aparecen como "cliente" en el universo actual.
_SQL_EMPRESAS_CD = """
SELECT E.ID_Empresa, E.Den_Comercial, E.Estado, E.ID_Tipo_Empresa,
       COUNT(*) AS maquinas
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
  AND S.Cuadricula IN ('SUR','SUROESTE','SUORESTE','OESTE','CENTRO','SMARTIN',
                       'CABA','CABA-N','CABA-S','CABA-O',
                       'NORTE1','NORTE2','NORTE3','NORTE4')
  AND (E.Den_Comercial LIKE 'CD%' OR E.Den_Comercial LIKE '%CDSA%')
GROUP BY E.ID_Empresa, E.Den_Comercial, E.Estado, E.ID_Tipo_Empresa
ORDER BY maquinas DESC
"""

# ¿ID_Tipo_Empresa distingue interna/cliente? Catálogo + distribución.
_SQL_TIPO_EMPRESA_CATALOGO = """
SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Tipo_Empresa' ORDER BY ORDINAL_POSITION
"""

_SQL_TIPO_EMPRESA_FILAS = "SELECT * FROM dbo.Tipo_Empresa ORDER BY 1"

_SQL_TIPOS_EN_UNIVERSO = """
SELECT E.ID_Tipo_Empresa, COUNT(DISTINCT E.ID_Empresa) AS empresas,
       COUNT(*) AS maquinas
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
  AND S.Cuadricula IN ('SUR','SUROESTE','SUORESTE','OESTE','CENTRO','SMARTIN',
                       'CABA','CABA-N','CABA-S','CABA-O',
                       'NORTE1','NORTE2','NORTE3','NORTE4')
GROUP BY E.ID_Tipo_Empresa
ORDER BY maquinas DESC
"""


def _dump(cursor: pyodbc.Cursor, titulo: str, sql: str) -> None:
    cursor.execute(sql)
    columnas = [d[0] for d in cursor.description]
    filas = list(cursor.fetchall())
    print(f"\n=== {titulo} ({len(filas)} filas) ===")
    print(f"  columnas: {columnas}")
    for f in filas:
        print(f"  {tuple(f)}")


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit("Falta SLA_MERCURIO_HOST en .env.")

    conn_str = build_mercurio_connection_string(settings)
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _dump(cursor, "Universo actual por Empresa.Estado", _SQL_POR_ESTADO_EMPRESA)
        _dump(cursor, "Clientes de baja que hoy aparecen (top 15)", _SQL_CLIENTES_DE_BAJA)
        _dump(cursor, "Empresas CD/CDSA en el universo", _SQL_EMPRESAS_CD)
        _dump(cursor, "Columnas de Tipo_Empresa", _SQL_TIPO_EMPRESA_CATALOGO)
        _dump(cursor, "Catálogo Tipo_Empresa", _SQL_TIPO_EMPRESA_FILAS)
        _dump(cursor, "Universo por ID_Tipo_Empresa", _SQL_TIPOS_EN_UNIVERSO)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
