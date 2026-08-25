"""Investiga si existe una señal de "última modificación" aprovechable en Siges
para el módulo `preventivos` (pregunta del usuario 2026-08-25: ¿se puede evitar
la consulta completa por zona con un chequeo liviano de "¿hay algo nuevo?").

Solo SELECTs de solo lectura, cuenta SiGesReadOnly, patrón de
explore_siges_preventivos_zona.py.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_preventivos_fecha_mod.py
"""

import time

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 30

# TABLE_TYPE real de cada tabla que le interesa al módulo (BASE TABLE vs VIEW):
# una VIEW emulada recalculada en bloque explicaría un Fecha_Mod pisado igual
# para todas las filas en cada refresh.
_SQL_TABLE_TYPE = """
SELECT TABLE_NAME, TABLE_TYPE
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME IN ('Sucursal', 'Empresa', 'Maquina', 'Incidente', 'Contadores', 'TipoPreventivo')
ORDER BY TABLE_NAME
"""

_SQL_COLUMNAS = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = ?
ORDER BY ORDINAL_POSITION
"""

# Distribución de Fecha_Mod/Usuario_Mod: si son pocos valores distintos y
# concentrados en pocos timestamps, es un refresh en bloque (inservible como
# señal de "esta fila cambió"); si son muchos valores distintos y recientes,
# es una señal real por fila.
_SQL_DISTRIBUCION_MOD = """
SELECT
    COUNT(*) AS total_filas,
    COUNT(DISTINCT {col_fecha}) AS fechas_distintas,
    COUNT(DISTINCT {col_usuario}) AS usuarios_distintos,
    MIN({col_fecha}) AS fecha_min,
    MAX({col_fecha}) AS fecha_max
FROM dbo.{tabla}
"""

_SQL_TOP_USUARIOS_MOD = """
SELECT TOP 10 {col_usuario} AS usuario, COUNT(*) AS filas, MAX({col_fecha}) AS ultima
FROM dbo.{tabla}
GROUP BY {col_usuario}
ORDER BY filas DESC
"""

# Filas con Fecha_Mod más reciente: si son de zonas/clientes distintos y
# fechas distintas entre sí (no todas el mismo instante), la señal es por fila.
_SQL_TOP_RECIENTES = """
SELECT TOP 10 {select_extra}, {col_fecha}, {col_usuario}
FROM dbo.{tabla}
ORDER BY {col_fecha} DESC
"""

# Watermark global candidato: última actividad de preventivos/contadores en
# TODA la base (sin filtrar por zona) — si esto es rápido, es la base de un
# chequeo de staleness barato.
_SQL_WATERMARK_PREVENTIVOS = """
SELECT MAX(Fecha_Ingreso) AS max_ingreso, MAX(Fecha_Cierre) AS max_cierre, COUNT(*) AS total
FROM dbo.Incidente
WHERE ID_Tipo_Incidente = 102
"""

_SQL_WATERMARK_CONTADORES = """
SELECT MAX(FechaTomaContador) AS max_toma, COUNT(*) AS total
FROM dbo.Contadores
WHERE Estado = 0
"""

_SQL_WATERMARK_MAQUINA_MOD = """
SELECT MAX(Fecha_Mod) AS max_mod, COUNT(*) AS total
FROM dbo.Maquina
"""


def _tiempo(cursor: pyodbc.Cursor, titulo: str, sql: str, params: tuple = ()) -> None:
    inicio = time.perf_counter()
    cursor.execute(sql, params) if params else cursor.execute(sql)
    fila = cursor.fetchone()
    columnas = [d[0] for d in cursor.description]
    elapsed = time.perf_counter() - inicio
    print(f"\n=== {titulo} ({elapsed:.3f}s) ===")
    print(f"  columnas: {columnas}")
    print(f"  {tuple(fila) if fila else None}")


def _dump_filas(cursor: pyodbc.Cursor, titulo: str, sql: str) -> None:
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

        _dump_filas(cursor, "TABLE_TYPE de tablas clave", _SQL_TABLE_TYPE)

        tablas = ["Sucursal", "Empresa", "Maquina", "Incidente", "Contadores", "TipoPreventivo"]
        for tabla in tablas:
            cursor.execute(_SQL_COLUMNAS, tabla)
            cols = [f.COLUMN_NAME for f in cursor.fetchall()]
            mod_cols = [c for c in cols if "mod" in c.lower() or "fecha" in c.lower()]
            print(f"\n=== {tabla}: columnas con 'mod'/'fecha' ===")
            print(f"  {mod_cols}")

        # Sucursal: ya documentado como "vista emulada" con Fecha_Mod pisado —
        # confirmar con dato fresco.
        _dump_filas(
            cursor,
            "Sucursal: distribución de Fecha_Mod/Usuario_Mod",
            _SQL_DISTRIBUCION_MOD.format(
                tabla="Sucursal", col_fecha="Fecha_Mod", col_usuario="Usuario_Mod"
            ),
        )
        _dump_filas(
            cursor,
            "Sucursal: TOP 10 usuarios de Fecha_Mod",
            _SQL_TOP_USUARIOS_MOD.format(
                tabla="Sucursal", col_fecha="Fecha_Mod", col_usuario="Usuario_Mod"
            ),
        )

        # Maquina: NO estaba marcada como vista emulada — confirmar si su
        # Fecha_Mod varía de verdad por fila (señal real) o también es un
        # refresh en bloque.
        _dump_filas(
            cursor,
            "Maquina: distribución de Fecha_Mod/Usuario_Mod",
            _SQL_DISTRIBUCION_MOD.format(
                tabla="Maquina", col_fecha="Fecha_Mod", col_usuario="Usuario_Mod"
            ),
        )
        _dump_filas(
            cursor,
            "Maquina: TOP 10 usuarios de Fecha_Mod",
            _SQL_TOP_USUARIOS_MOD.format(
                tabla="Maquina", col_fecha="Fecha_Mod", col_usuario="Usuario_Mod"
            ),
        )
        _dump_filas(
            cursor,
            "Maquina: 10 filas con Fecha_Mod más reciente",
            _SQL_TOP_RECIENTES.format(
                tabla="Maquina",
                col_fecha="Fecha_Mod",
                col_usuario="Usuario_Mod",
                select_extra="ID_Maquina, ID_Sucursal, ID_Estado_Maquina, Estado",
            ),
        )

        # Watermarks candidatos para un chequeo de staleness barato.
        _tiempo(
            cursor,
            "Watermark: último preventivo (tipo 102) global",
            _SQL_WATERMARK_PREVENTIVOS,
        )
        _tiempo(cursor, "Watermark: última toma de contador global", _SQL_WATERMARK_CONTADORES)
        _tiempo(cursor, "Watermark: Fecha_Mod máxima de Maquina", _SQL_WATERMARK_MAQUINA_MOD)

    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
