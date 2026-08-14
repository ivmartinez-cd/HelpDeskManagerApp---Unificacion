"""Ronda 2 de exploración para "preventivos por zona" (ver
explore_siges_preventivos_zona.py). Hallazgos de ronda 1 que motivan esta:
`dbo.Distribucion` es catálogo de transportistas/técnicos (NO zonas), pero
`Sucursal` tiene `Distribucion` (int, null) y `Cuadricula` (varchar 10) sin
valores vistos; `Sucursal.TipoPreventivo` → `TipoPreventivo(Tipo, Dias)` pinta
ser la frecuencia; preventivo = Tipo_Incidente 102. Solo SELECTs.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_ronda2.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

# ¿Qué guarda Sucursal.Distribucion? Valores + cuántas sucursales activas cada uno,
# cruzado contra el catálogo Distribucion por si el int apunta ahí.
_SQL_SUC_DISTRIBUCION = """
SELECT S.Distribucion AS valor, D.Descripcion AS en_catalogo_distribucion,
       COUNT(*) AS sucursales,
       SUM(CASE WHEN S.Estado = 0 THEN 1 ELSE 0 END) AS activas
FROM dbo.Sucursal S
LEFT JOIN dbo.Distribucion D ON D.Id = S.Distribucion
GROUP BY S.Distribucion, D.Descripcion
ORDER BY sucursales DESC
"""

_SQL_SUC_CUADRICULA = """
SELECT S.Cuadricula AS valor, COUNT(*) AS sucursales,
       SUM(CASE WHEN S.Estado = 0 THEN 1 ELSE 0 END) AS activas
FROM dbo.Sucursal S
GROUP BY S.Cuadricula
ORDER BY sucursales DESC
"""

# Búsqueda global: cualquier tabla o columna que suene a zona/cuadrícula.
_SQL_COLUMNAS_ZONA = """
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%zona%' OR COLUMN_NAME LIKE '%cuadric%'
   OR TABLE_NAME LIKE '%zona%' OR TABLE_NAME LIKE '%cuadric%'
ORDER BY TABLE_NAME, COLUMN_NAME
"""

# ¿Quién referencia el catálogo Frecuencia?
_SQL_COLUMNAS_FRECUENCIA = """
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE COLUMN_NAME LIKE '%recuencia%'
ORDER BY TABLE_NAME, COLUMN_NAME
"""

_SQL_COLUMNAS_INCIDENTE = """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Incidente'
ORDER BY ORDINAL_POSITION
"""

_SQL_ESTADO_INCIDENTE = "SELECT Id, Descripcion, Estado FROM dbo.Estado_Incidente ORDER BY Id"

# Frecuencia real del parque: TipoPreventivo por sucursal activa con máquinas activas.
_SQL_TIPO_PREV_POR_SUCURSAL = """
SELECT S.TipoPreventivo AS tipo, TP.Dias AS dias,
       COUNT(DISTINCT S.Id_Sucursal) AS sucursales_activas,
       COUNT(M.ID_Maquina) AS maquinas_activas
FROM dbo.Sucursal S
LEFT JOIN dbo.TipoPreventivo TP ON TP.Tipo = S.TipoPreventivo
LEFT JOIN dbo.Maquina M
    ON M.ID_Sucursal = S.Id_Sucursal
   AND M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)
WHERE S.Estado = 0
GROUP BY S.TipoPreventivo, TP.Dias
ORDER BY maquinas_activas DESC
"""

# ¿Los preventivos (102) se siguen cargando? Volumen por año y estados usados.
_SQL_PREVENTIVOS_POR_ANIO = """
SELECT YEAR(I.Fecha_Ingreso) AS anio, COUNT(*) AS incidentes
FROM dbo.Incidente I
WHERE I.ID_Tipo_Incidente = 102 AND I.Fecha_Ingreso >= '2020-01-01'
GROUP BY YEAR(I.Fecha_Ingreso)
ORDER BY anio
"""

_SQL_PREVENTIVOS_POR_ESTADO = """
SELECT EI.Id, EI.Descripcion, COUNT(*) AS incidentes
FROM dbo.Incidente I
INNER JOIN dbo.Estado_Incidente EI ON EI.Id = I.ID_Estado_Incidente
WHERE I.ID_Tipo_Incidente = 102 AND I.Fecha_Ingreso >= '2024-01-01'
GROUP BY EI.Id, EI.Descripcion
ORDER BY incidentes DESC
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
        _dump(cursor, "Sucursal.Distribucion: valores", _SQL_SUC_DISTRIBUCION)
        _dump(cursor, "Sucursal.Cuadricula: valores", _SQL_SUC_CUADRICULA)
        _dump(cursor, "Columnas/tablas %zona%/%cuadric% en todo el esquema", _SQL_COLUMNAS_ZONA)
        _dump(cursor, "Columnas %recuencia% en todo el esquema", _SQL_COLUMNAS_FRECUENCIA)
        _dump(cursor, "Columnas de Incidente", _SQL_COLUMNAS_INCIDENTE)
        _dump(cursor, "Catálogo Estado_Incidente", _SQL_ESTADO_INCIDENTE)
        _dump(
            cursor,
            "TipoPreventivo por sucursal activa (máquinas activas)",
            _SQL_TIPO_PREV_POR_SUCURSAL,
        )
        _dump(
            cursor, "Incidentes tipo 102 (Preventivo) por año desde 2020", _SQL_PREVENTIVOS_POR_ANIO
        )
        _dump(cursor, "Incidentes 102 desde 2024 por estado", _SQL_PREVENTIVOS_POR_ESTADO)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
