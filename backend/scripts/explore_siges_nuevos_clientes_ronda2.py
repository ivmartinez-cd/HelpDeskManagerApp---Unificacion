"""Ronda 2 de `explore_siges_nuevos_clientes.py` (solo lectura, misma cuenta
SiGesReadOnly). Corrige los errores de la ronda 1 (nombres reales de columnas de
Maquina/Incidente) y explora las tablas de historial/movimiento de máquinas
(`MaquinaHist`, `Auditlog`, `ObjetoHist`, `AnexoMovimientoLog`) y `Anexo.FechaInicio`
como señal de "cliente nuevo / instalación nueva".

Uso (dentro del contenedor backend): uv run python scripts/explore_siges_nuevos_clientes_ronda2.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60
_SQL_ROLES = "SELECT IS_ROLEMEMBER('db_datawriter') AS w, IS_ROLEMEMBER('db_owner') AS o"
_SQL_COLUMNAS = (
    "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
    "WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=? ORDER BY ORDINAL_POSITION"
)
_SQL_COUNT = "SELECT COUNT(*) AS n FROM dbo.[{t}]"


def _imprimir(cursor: pyodbc.Cursor, titulo: str, sql: str, params: tuple = ()) -> None:
    print(f"\n--- {titulo} ---")
    try:
        cursor.execute(sql, params)
        filas = cursor.fetchall()
    except pyodbc.Error as exc:  # exploración: seguimos con la siguiente consulta
        print(f"  ERROR: {exc}")
        return
    print("  " + " | ".join(d[0] for d in cursor.description))
    for f in filas:
        print("  " + " | ".join(str(v) for v in f))
    print(f"  ({len(filas)} fila/s)")


def _columnas(cursor: pyodbc.Cursor, tabla: str) -> None:
    cursor.execute(_SQL_COLUMNAS, (tabla,))
    cols = [f"{c.COLUMN_NAME}:{c.DATA_TYPE}" for c in cursor.fetchall()]
    try:
        cursor.execute(_SQL_COUNT.format(t=tabla))
        n = cursor.fetchone().n
    except pyodbc.Error as exc:
        n = f"ERROR {exc}"
    print(f"\n{tabla} ({n} filas): {', '.join(cols)}")


def _ronda_columnas(cursor: pyodbc.Cursor) -> None:
    print("=== Columnas completas ===")
    for t in (
        "Maquina",
        "Incidente",
        "MaquinaHist",
        "Auditlog",
        "ObjetoHist",
        "AnexoMovimientoLog",
    ):
        _columnas(cursor, t)


def _ronda_hist(cursor: pyodbc.Cursor) -> None:
    print("\n=== Historial de máquinas ===")
    _imprimir(
        cursor,
        "MaquinaHist: 10 filas más recientes (TOP por PK desc)",
        "SELECT TOP 10 * FROM dbo.MaquinaHist ORDER BY 1 DESC",
    )
    _imprimir(cursor, "ObjetoHist: 5 filas", "SELECT TOP 5 * FROM dbo.ObjetoHist ORDER BY 1 DESC")
    _imprimir(cursor, "Auditlog: 5 filas", "SELECT TOP 5 * FROM dbo.Auditlog ORDER BY 1 DESC")
    _imprimir(
        cursor,
        "AnexoMovimientoLog: 5 filas",
        "SELECT TOP 5 * FROM dbo.AnexoMovimientoLog ORDER BY 1 DESC",
    )


def _ronda_anexos(cursor: pyodbc.Cursor) -> None:
    print("\n=== Anexos nuevos (FechaInicio) ===")
    _imprimir(
        cursor,
        "Anexos con FechaInicio en últimos 6 meses, por mes",
        "SELECT CONVERT(char(7), FechaInicio, 120) AS mes, COUNT(*) AS n FROM dbo.Anexo "
        "WHERE FechaInicio >= DATEADD(month,-6,GETDATE()) GROUP BY CONVERT(char(7), FechaInicio, 120) ORDER BY mes",  # noqa: E501
    )
    _imprimir(
        cursor,
        "Anexo: columnas y 5 más recientes por FechaInicio",
        "SELECT TOP 5 * FROM dbo.Anexo ORDER BY FechaInicio DESC",
    )
    _imprimir(
        cursor,
        "Contrato: 5 más recientes por FechaFirmaContrato",
        "SELECT TOP 5 * FROM dbo.Contrato ORDER BY FechaFirmaContrato DESC",
    )


def _ronda_instalaciones(cursor: pyodbc.Cursor) -> None:
    print("\n=== Incidentes tipo 103 (muestra) ===")
    _imprimir(
        cursor,
        "10 incidentes tipo 103 recientes (todas las columnas)",
        "SELECT TOP 10 * FROM dbo.Incidente WHERE ID_Tipo_Incidente = 103 ORDER BY Fecha_Ingreso DESC",  # noqa: E501
    )
    _imprimir(
        cursor,
        "Incidentes 103 recientes de clientes nuevos (ID_Empresa >= 1395)",
        "SELECT I.ID_Incidente, I.Fecha_Ingreso, I.ID_Empresa, E.Den_Comercial, I.ID_Sucursal, I.ID_Maquina "  # noqa: E501
        "FROM dbo.Incidente I JOIN dbo.Empresa E ON E.ID_Empresa=I.ID_Empresa "
        "WHERE I.ID_Tipo_Incidente=103 AND I.ID_Empresa >= 1395 ORDER BY I.Fecha_Ingreso DESC",
    )


def main() -> None:
    conn = pyodbc.connect(
        build_mercurio_connection_string(get_settings()), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    try:
        conn.timeout = _TIMEOUT_SECONDS
        cursor = conn.cursor()
        cursor.execute(_SQL_ROLES)
        r = cursor.fetchone()
        if r.w or r.o:
            raise SystemExit("La cuenta tiene permisos de escritura: abortando.")
        _ronda_columnas(cursor)
        _ronda_hist(cursor)
        _ronda_anexos(cursor)
        _ronda_instalaciones(cursor)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
