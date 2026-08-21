"""Explora Siges/MERCURIO (cuenta SiGesReadOnly) buscando una señal confiable de
"cliente nuevo" / "instalación nueva", para evaluar una alerta de calendario de
onboarding (mensajes de instalación, etc.). Solo lectura: mismo patrón que
`explore_siges_planificacion.py` (verifica roles antes de leer, conexión efímera,
`autocommit=True`, `close()` en `finally`).

Rondas:
  1. Columnas de fecha/alta en Empresa, Sucursal, Maquina, Anexo, Contrato,
     MaquinaMotivoMov, Incidente (INFORMATION_SCHEMA).
  2. Empresa clientes reales (ID_Tipo_Empresa IN (101,102)): ¿hay fecha de alta?
     Si hay, distribución reciente; si no, últimos IDs (¿son secuenciales?).
  3. Incidentes tipo 103 'Instalación-Desinstalación' por mes (últimos 6 meses) + muestra.
  4. Máquinas en estado 210 'Alta Solicitada' y fechas de Maquina recientes.
  5. "Primera actividad" por empresa (MIN Contadores.FechaTomaContador / MIN
     Incidente.Fecha_Ingreso) — empresas cuya primera actividad cae en los últimos 6 meses.

Uso (dentro del contenedor backend): uv run python scripts/explore_siges_nuevos_clientes.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

_SQL_IDENTIDAD = "SELECT SUSER_SNAME() AS login_name, DB_NAME() AS db_name"
_SQL_ROLES = (
    "SELECT IS_ROLEMEMBER('db_datareader') AS r, IS_ROLEMEMBER('db_datawriter') AS w, "
    "IS_ROLEMEMBER('db_owner') AS o"
)
_SQL_COLUMNAS = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ?
ORDER BY ORDINAL_POSITION
"""
_TABLAS = [
    "Empresa",
    "Sucursal",
    "Maquina",
    "Anexo",
    "Contrato",
    "MaquinaMotivoMov",
    "Incidente",
    "MaquinaInstalacion",
]
_PALABRAS_CLAVE = ("fecha", "alta", "creac", "ingreso", "instal", "inicio", "date", "vigen")


def _verificar(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_IDENTIDAD)
    i = cursor.fetchone()
    cursor.execute(_SQL_ROLES)
    r = cursor.fetchone()
    print(f"Conectado como {i.login_name} db={i.db_name} reader={r.r} writer={r.w} owner={r.o}")
    if r.w or r.o:
        raise SystemExit("La cuenta tiene permisos de escritura: abortando exploración.")


def _imprimir(cursor: pyodbc.Cursor, titulo: str, sql: str, params: tuple = ()) -> None:
    print(f"\n--- {titulo} ---")
    try:
        cursor.execute(sql, params)
        filas = cursor.fetchall()
    except pyodbc.Error as exc:  # seguimos con la siguiente consulta, es exploración
        print(f"  ERROR: {exc}")
        return
    cols = [d[0] for d in cursor.description]
    print("  " + " | ".join(cols))
    for f in filas:
        print("  " + " | ".join(str(v) for v in f))
    print(f"  ({len(filas)} fila/s)")


def _ronda1_columnas(cursor: pyodbc.Cursor) -> dict[str, list[tuple[str, str]]]:
    print("\n=== RONDA 1: columnas de fecha/alta por tabla ===")
    resultado: dict[str, list[tuple[str, str]]] = {}
    for tabla in _TABLAS:
        cursor.execute(_SQL_COLUMNAS, (tabla,))
        cols = [(c.COLUMN_NAME, c.DATA_TYPE) for c in cursor.fetchall()]
        resultado[tabla] = cols
        interesantes = [
            (n, t)
            for n, t in cols
            if t in ("datetime", "date", "smalldatetime", "datetime2")
            or any(p in n.lower() for p in _PALABRAS_CLAVE)
        ]
        print(f"\n{tabla}: {len(cols)} columnas; fecha/alta-like: {interesantes}")
    return resultado


def _ronda2_empresa(cursor: pyodbc.Cursor, cols: list[tuple[str, str]]) -> None:
    print("\n=== RONDA 2: Empresa clientes reales (101/102) ===")
    fechas = [n for n, t in cols if t in ("datetime", "date", "smalldatetime", "datetime2")]
    for col in fechas:
        _imprimir(
            cursor,
            f"Empresa.{col}: rango y cuántas en últimos 90/365 días (clientes reales)",
            f"SELECT MIN([{col}]) AS min_v, MAX([{col}]) AS max_v, "
            f"SUM(CASE WHEN [{col}] >= DATEADD(day,-90,GETDATE()) THEN 1 ELSE 0 END) AS ult_90d, "
            f"SUM(CASE WHEN [{col}] >= DATEADD(day,-365,GETDATE()) THEN 1 ELSE 0 END) AS ult_365d, "
            f"SUM(CASE WHEN [{col}] IS NULL THEN 1 ELSE 0 END) AS nulos, COUNT(*) AS total "
            "FROM dbo.Empresa WHERE ID_Tipo_Empresa IN (101,102)",
        )
    _imprimir(
        cursor,
        "Últimos 15 ID_Empresa de clientes reales (¿IDs secuenciales = orden de alta?)",
        "SELECT TOP 15 ID_Empresa, Den_Comercial, ID_Tipo_Empresa, Estado "
        "FROM dbo.Empresa WHERE ID_Tipo_Empresa IN (101,102) ORDER BY ID_Empresa DESC",
    )


def _ronda3_instalaciones(cursor: pyodbc.Cursor) -> None:
    print("\n=== RONDA 3: Incidente tipo 103 (Instalación-Desinstalación) ===")
    _imprimir(
        cursor,
        "Incidentes tipo 103 por mes, últimos 6 meses",
        "SELECT CONVERT(char(7), Fecha_Ingreso, 120) AS mes, COUNT(*) AS n "
        "FROM dbo.Incidente WHERE ID_Tipo_Incidente = 103 "
        "AND Fecha_Ingreso >= DATEADD(month,-6,GETDATE()) "
        "GROUP BY CONVERT(char(7), Fecha_Ingreso, 120) ORDER BY mes",
    )
    _imprimir(
        cursor,
        "Muestra de 10 incidentes tipo 103 recientes",
        "SELECT TOP 10 I.ID_Incidente, I.Fecha_Ingreso, I.ID_Empresa, E.Den_Comercial, "
        "I.ID_Sucursal, I.ID_Estado_Incidente, LEFT(CAST(I.Descripcion AS varchar(120)),120) AS descr "  # noqa: E501
        "FROM dbo.Incidente I LEFT JOIN dbo.Empresa E ON E.ID_Empresa = I.ID_Empresa "
        "WHERE I.ID_Tipo_Incidente = 103 ORDER BY I.Fecha_Ingreso DESC",
    )


def _ronda4_maquinas(cursor: pyodbc.Cursor, cols: list[tuple[str, str]]) -> None:
    print("\n=== RONDA 4: Maquina — altas ===")
    _imprimir(
        cursor,
        "Máquinas por estado 210 'Alta Solicitada' / 211 'En Garantia' (clientes reales)",
        "SELECT M.ID_Estado_Maquina, EM.Descripcion, COUNT(*) AS n "
        "FROM dbo.Maquina M JOIN dbo.Estado_Maquina EM ON EM.ID_Estado_Maquina = M.ID_Estado_Maquina "  # noqa: E501
        "JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa "
        "WHERE E.ID_Tipo_Empresa IN (101,102) AND M.ID_Estado_Maquina IN (210, 211) "
        "GROUP BY M.ID_Estado_Maquina, EM.Descripcion",
    )
    fechas = [n for n, t in cols if t in ("datetime", "date", "smalldatetime", "datetime2")]
    for col in fechas:
        _imprimir(
            cursor,
            f"Maquina.{col}: rango y últimos 90 días (clientes reales)",
            f"SELECT MIN([{col}]) AS min_v, MAX([{col}]) AS max_v, "
            f"SUM(CASE WHEN [{col}] >= DATEADD(day,-90,GETDATE()) THEN 1 ELSE 0 END) AS ult_90d, "
            f"SUM(CASE WHEN [{col}] IS NULL THEN 1 ELSE 0 END) AS nulos, COUNT(*) AS total "
            "FROM dbo.Maquina M JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa "
            "WHERE E.ID_Tipo_Empresa IN (101,102)",
        )
    _imprimir(
        cursor,
        "MaquinaMotivoMov: muestra de 10 filas",
        "SELECT TOP 10 * FROM dbo.MaquinaMotivoMov",
    )


def _ronda5_primera_actividad(cursor: pyodbc.Cursor) -> None:
    print("\n=== RONDA 5: primera actividad por empresa (proxy de alta) ===")
    _imprimir(
        cursor,
        "Empresas cuyo primer incidente cae en los últimos 6 meses",
        "SELECT TOP 30 E.ID_Empresa, E.Den_Comercial, MIN(I.Fecha_Ingreso) AS primer_inc, "
        "COUNT(*) AS n_inc "
        "FROM dbo.Incidente I JOIN dbo.Empresa E ON E.ID_Empresa = I.ID_Empresa "
        "WHERE E.ID_Tipo_Empresa IN (101,102) "
        "GROUP BY E.ID_Empresa, E.Den_Comercial "
        "HAVING MIN(I.Fecha_Ingreso) >= DATEADD(month,-6,GETDATE()) "
        "ORDER BY primer_inc DESC",
    )
    _imprimir(
        cursor,
        "Empresas cuya primera toma de contador cae en los últimos 6 meses",
        "SELECT TOP 30 E.ID_Empresa, E.Den_Comercial, MIN(C.FechaTomaContador) AS primera_toma, "
        "COUNT(DISTINCT M.ID_Maquina) AS maquinas "
        "FROM dbo.Contadores C JOIN dbo.Maquina M ON M.ID_Maquina = C.ID_Maquina "
        "JOIN dbo.Empresa E ON E.ID_Empresa = M.ID_Empresa "
        "WHERE E.ID_Tipo_Empresa IN (101,102) "
        "GROUP BY E.ID_Empresa, E.Den_Comercial "
        "HAVING MIN(C.FechaTomaContador) >= DATEADD(month,-6,GETDATE()) "
        "ORDER BY primera_toma DESC",
    )
    _imprimir(
        cursor,
        "Sucursales: últimas 10 por ID (¿hay fecha?)",
        "SELECT TOP 10 * FROM dbo.Sucursal ORDER BY ID_Sucursal DESC",
    )


def main() -> None:
    settings = get_settings()
    conn = pyodbc.connect(
        build_mercurio_connection_string(settings), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    try:
        conn.timeout = _TIMEOUT_SECONDS
        cursor = conn.cursor()
        _verificar(cursor)
        cols = _ronda1_columnas(cursor)
        _ronda2_empresa(cursor, cols["Empresa"])
        _ronda3_instalaciones(cursor)
        _ronda4_maquinas(cursor, cols["Maquina"])
        _ronda5_primera_actividad(cursor)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
