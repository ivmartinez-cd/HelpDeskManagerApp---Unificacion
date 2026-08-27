"""Explora dbo.Instancia / dbo.Instancia_Motivos para determinar si guardan
el historial de cambios de estado de un incidente (pantalla legacy "LISTA DE
INSTANCIAS" de Canal Directo) — paso previo para excluir de "Incidentes sin
consultar" a los que ya tuvieron una visita previa (pasaron por En Curso
antes de volver a Derivado).

Solo SELECTs. Cuenta SiGesReadOnly, autocommit=True, close() explícito en
finally. Mismo patrón que explore_siges_incidentes_sin_cerrar.py.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_instancia.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

# El incidente 842550 (servicio técnico 842550-6, Banco Credicoop) es el de
# la captura real que mostró el usuario: Pendiente -> Derivado -> En Curso ->
# En Espera de Repuestos -> Derivado (5 instancias, ya tuvo una visita).
_ID_INCIDENTE_CAPTURA = 842550

_SQL_COLUMNAS = """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = ?
ORDER BY ORDINAL_POSITION
"""

_SQL_MUESTRA_CAPTURA = """
SELECT TOP 20 * FROM dbo.Instancia WHERE ID_Incidente = ? ORDER BY 1
"""

_SQL_MUESTRA_DERIVADOS = """
SELECT TOP 20 * FROM dbo.Instancia
WHERE ID_Incidente IN (
    SELECT TOP 5 ID_Incidente FROM dbo.Incidente
    WHERE ID_Estado_Incidente = 200 AND ID_Tipo_Incidente IN (101, 108)
)
ORDER BY ID_Incidente
"""


def _columnas(cursor: pyodbc.Cursor, tabla: str) -> None:
    try:
        cursor.execute(_SQL_COLUMNAS, (tabla,))
        filas = list(cursor.fetchall())
        print(f"\n=== Columnas de dbo.{tabla} ({len(filas)}) ===")
        for f in filas:
            print(f"  {f.COLUMN_NAME}  ({f.DATA_TYPE}, nullable={f.IS_NULLABLE})")
    except pyodbc.Error as e:
        print(f"\n=== dbo.{tabla} — error al listar columnas: {e} ===")


def _ejecutar(cursor: pyodbc.Cursor, sql: str, params: tuple[object, ...]) -> None:
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)


def _muestra(cursor: pyodbc.Cursor, sql: str, titulo: str, params: tuple[object, ...] = ()) -> None:
    try:
        _ejecutar(cursor, sql, params)
        filas = list(cursor.fetchall())
        if not filas:
            print(f"\n=== {titulo} — sin filas ===")
            return
        cols = [d[0] for d in cursor.description]
        print(f"\n=== {titulo} ({len(filas)} filas) ===")
        print("  Columnas:", cols)
        for f in filas:
            print(" ", dict(zip(cols, f, strict=True)))
    except pyodbc.Error as e:
        print(f"\n=== {titulo} — error: {e} ===")


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit(
            "Falta SLA_MERCURIO_HOST en .env — no hay acceso a MERCURIO desde este entorno."
        )

    conn_str = build_mercurio_connection_string(settings)
    print("Conectando a MERCURIO…")
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _columnas(cursor, "Instancia")
        _columnas(cursor, "Instancia_Motivos")
        _muestra(
            cursor,
            _SQL_MUESTRA_CAPTURA,
            f"dbo.Instancia — incidente {_ID_INCIDENTE_CAPTURA} (captura)",
            (_ID_INCIDENTE_CAPTURA,),
        )
        _muestra(
            cursor, _SQL_MUESTRA_DERIVADOS, "dbo.Instancia — muestra de 5 incidentes en estado 200"
        )
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
