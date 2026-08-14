"""Explora SiGesReadOnly para la feature "preventivos por zona de distribución".
Solo SELECTs parametrizados, cuenta de solo lectura, patrón de
explore_siges_parque_pst.py (conexión efímera, autocommit=True, close() en finally).

Ronda 1 — preguntas:
  1. ¿`dbo.Distribucion` es el catálogo de ZONAS (SUR/SURESTE/NORTE 1-4/CABA...) o de
     transportistas, como dice hoy el catálogo de datos?
  2. Columnas COMPLETAS de `Empresa` y `Sucursal` (nunca se volcaron al doc) buscando
     el FK de zona (`ID_Distribucion` o similar) en una, otra o ambas.
  3. Catálogo completo de `Tipo_Incidente` (deuda del módulo sla: qué son 101 y 108,
     y cuál/es son preventivos).
  4. Columnas + filas de `Frecuencia` y `TipoPreventivo` (catálogos chicos).
  5. Columnas + muestra de `IncidentePreventivo` y de las VIEWs `Mantenimiento`,
     `Contrato`, `Anexo` — dónde vive "cada cuánto le toca el preventivo".

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_zona.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 30

_SQL_DISTRIBUCION = "SELECT Id, Descripcion, Cuit, Estado FROM dbo.Distribucion ORDER BY Id"

_SQL_COLUMNAS = """
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = ?
ORDER BY ORDINAL_POSITION
"""

_SQL_TIPO_INCIDENTE = "SELECT * FROM dbo.Tipo_Incidente ORDER BY 1"

_SQL_FRECUENCIA = "SELECT * FROM dbo.Frecuencia ORDER BY 1"

_SQL_TIPO_PREVENTIVO = "SELECT * FROM dbo.TipoPreventivo ORDER BY 1"

_SQL_COUNT = "SELECT COUNT(*) AS total FROM dbo.{tabla}"

_SQL_MUESTRA = "SELECT TOP 5 * FROM dbo.{tabla}"

# Tablas cuyo COUNT + TOP 5 queremos ver además de las columnas.
_TABLAS_MUESTRA = ["IncidentePreventivo", "Mantenimiento"]

# Tablas/vistas de las que solo queremos el set de columnas (muestras después,
# cuando sepamos qué columnas pedir).
_TABLAS_SOLO_COLUMNAS = ["Empresa", "Sucursal", "Contrato", "Anexo"]


def _dump_filas(cursor: pyodbc.Cursor, titulo: str, sql: str) -> None:
    cursor.execute(sql)
    columnas = [d[0] for d in cursor.description]
    filas = list(cursor.fetchall())
    print(f"\n=== {titulo} ({len(filas)} filas) ===")
    print(f"  columnas: {columnas}")
    for f in filas:
        print(f"  {tuple(f)}")


def _dump_columnas(cursor: pyodbc.Cursor, tabla: str) -> None:
    cursor.execute(_SQL_COLUMNAS, tabla)
    filas = list(cursor.fetchall())
    print(f"\n=== Columnas de {tabla} ({len(filas)}) ===")
    for f in filas:
        largo = f" ({f.CHARACTER_MAXIMUM_LENGTH})" if f.CHARACTER_MAXIMUM_LENGTH else ""
        print(f"  {f.COLUMN_NAME}: {f.DATA_TYPE}{largo} null={f.IS_NULLABLE}")


def _dump_count_y_muestra(cursor: pyodbc.Cursor, tabla: str) -> None:
    cursor.execute(_SQL_COUNT.format(tabla=tabla))
    total = cursor.fetchone().total
    print(f"\n=== {tabla}: {total} filas — TOP 5 ===")
    cursor.execute(_SQL_MUESTRA.format(tabla=tabla))
    columnas = [d[0] for d in cursor.description]
    print(f"  columnas: {columnas}")
    for f in cursor.fetchall():
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
        _dump_filas(cursor, "dbo.Distribucion", _SQL_DISTRIBUCION)
        for tabla in _TABLAS_SOLO_COLUMNAS:
            _dump_columnas(cursor, tabla)
        _dump_filas(cursor, "dbo.Tipo_Incidente completo", _SQL_TIPO_INCIDENTE)
        _dump_filas(cursor, "dbo.Frecuencia completo", _SQL_FRECUENCIA)
        _dump_filas(cursor, "dbo.TipoPreventivo completo", _SQL_TIPO_PREVENTIVO)
        for tabla in _TABLAS_MUESTRA:
            _dump_columnas(cursor, tabla)
            _dump_count_y_muestra(cursor, tabla)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
