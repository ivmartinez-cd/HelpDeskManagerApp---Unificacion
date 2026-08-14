"""Ronda 6: en el universo local no hay Empresa.Estado=1 (ronda 5) — el
"cliente de baja" que ve el usuario tiene que ser otra cosa. Se busca el
criterio real: semántica de ID_Tipo_Empresa (sin catálogo en DB), estados de
máquina que dominan el universo, y qué son las 201 máquinas de CD1. Solo
SELECTs.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_ronda6.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

_ZONAS = """('SUR','SUROESTE','SUORESTE','OESTE','CENTRO','SMARTIN',
             'CABA','CABA-N','CABA-S','CABA-O','NORTE1','NORTE2','NORTE3','NORTE4')"""

_SQL_TIPOS = f"""
SELECT E.ID_Tipo_Empresa, COUNT(DISTINCT E.ID_Empresa) AS empresas,
       COUNT(*) AS maquinas, MIN(E.Den_Comercial) AS ejemplo
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
  AND S.Cuadricula IN {_ZONAS}
GROUP BY E.ID_Tipo_Empresa
ORDER BY maquinas DESC
"""

# Semántica global de ID_Tipo_Empresa (no solo el universo local): ejemplos.
_SQL_TIPOS_GLOBAL = """
SELECT E.ID_Tipo_Empresa, COUNT(*) AS empresas,
       SUM(CASE WHEN E.Estado = 0 THEN 1 ELSE 0 END) AS activas,
       MIN(E.Den_Comercial) AS ejemplo1, MAX(E.Den_Comercial) AS ejemplo2
FROM dbo.Empresa E
GROUP BY E.ID_Tipo_Empresa
ORDER BY empresas DESC
"""

_SQL_ESTADOS_UNIVERSO = f"""
SELECT EM.Id, EM.Descripcion, COUNT(*) AS maquinas
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Estado_Maquina EM ON EM.Id = M.ID_Estado_Maquina
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
  AND S.Cuadricula IN {_ZONAS}
GROUP BY EM.Id, EM.Descripcion
ORDER BY maquinas DESC
"""

_SQL_CD1_DETALLE = f"""
SELECT S.descripcion AS sucursal, S.Cuadricula, EM.Descripcion AS estado_maquina,
       COUNT(*) AS maquinas
FROM dbo.Maquina M
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = M.ID_Sucursal
INNER JOIN dbo.Estado_Maquina EM ON EM.Id = M.ID_Estado_Maquina
WHERE S.Estado = 0 AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
  AND S.Cuadricula IN {_ZONAS}
  AND M.ID_Empresa = 1
GROUP BY S.descripcion, S.Cuadricula, EM.Descripcion
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
        _dump(cursor, "Universo local por ID_Tipo_Empresa", _SQL_TIPOS)
        _dump(cursor, "ID_Tipo_Empresa global (toda Empresa)", _SQL_TIPOS_GLOBAL)
        _dump(cursor, "Universo local por Estado_Maquina", _SQL_ESTADOS_UNIVERSO)
        _dump(cursor, "CD1 (ID_Empresa=1): sucursal/estado de sus máquinas", _SQL_CD1_DETALLE)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
