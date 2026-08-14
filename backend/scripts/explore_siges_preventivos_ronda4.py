"""Ronda 4 de exploración para "preventivos por zona": ¿hay una regla de DATOS
para distinguir zonas locales (técnicos propios) de zonas de PST del interior,
sin hardcodear la lista de cuadrículas? Hipótesis: `Sucursal.ID_Prestador`
(NULL o Canal Directo = local; PST = interior). Solo SELECTs.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_ronda4.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

# Por cuadrícula: cuántas sucursales activas tienen prestador NULL vs asignado,
# y el prestador más frecuente.
_SQL_PRESTADOR_POR_CUADRICULA = """
SELECT S.Cuadricula,
       COUNT(*) AS activas,
       SUM(CASE WHEN S.ID_Prestador IS NULL THEN 1 ELSE 0 END) AS sin_prestador,
       SUM(CASE WHEN S.ID_Prestador IS NOT NULL THEN 1 ELSE 0 END) AS con_prestador
FROM dbo.Sucursal S
WHERE S.Estado = 0
GROUP BY S.Cuadricula
ORDER BY activas DESC
"""

# Prestadores más frecuentes en las cuadrículas "locales" nombradas por el usuario.
_SQL_PRESTADORES_EN_LOCALES = """
SELECT TOP 15 E.ID_Empresa, E.Den_Comercial, COUNT(*) AS sucursales
FROM dbo.Sucursal S
INNER JOIN dbo.Empresa E ON E.ID_Empresa = S.ID_Prestador
WHERE S.Estado = 0
  AND S.Cuadricula IN ('SUR', 'SUROESTE', 'OESTE', 'CENTRO', 'SMARTIN',
                       'CABA', 'CABA-N', 'CABA-S', 'CABA-O',
                       'NORTE1', 'NORTE2', 'NORTE3', 'NORTE4')
GROUP BY E.ID_Empresa, E.Den_Comercial
ORDER BY sucursales DESC
"""

# Y al revés: prestadores más frecuentes en INTERIOR.
_SQL_PRESTADORES_EN_INTERIOR = """
SELECT TOP 10 E.ID_Empresa, E.Den_Comercial, COUNT(*) AS sucursales
FROM dbo.Sucursal S
INNER JOIN dbo.Empresa E ON E.ID_Empresa = S.ID_Prestador
WHERE S.Estado = 0 AND S.Cuadricula = 'INTERIOR'
GROUP BY E.ID_Empresa, E.Den_Comercial
ORDER BY sucursales DESC
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
        _dump(cursor, "Prestador NULL/asignado por cuadrícula", _SQL_PRESTADOR_POR_CUADRICULA)
        _dump(cursor, "Prestadores en cuadrículas locales", _SQL_PRESTADORES_EN_LOCALES)
        _dump(cursor, "Prestadores en INTERIOR", _SQL_PRESTADORES_EN_INTERIOR)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
