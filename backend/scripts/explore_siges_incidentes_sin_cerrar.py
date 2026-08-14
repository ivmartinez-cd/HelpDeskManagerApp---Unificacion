"""Explora SiGesReadOnly para determinar la definición operativa de
"incidente pendiente a cerrar" — paso previo bloqueante antes de construir
la feature de planillas pendientes por PST.

Solo SELECTs parametrizados. Cuenta SiGesReadOnly, autocommit=True,
close() explícito en finally. Mismo patrón que explore_siges_parque_pst.py.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_incidentes_sin_cerrar.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60
_TIPOS_ST = (101, 108)

_SQL_CATALOGO_ESTADO = """
SELECT Id, Descripcion FROM dbo.Estado_Incidente ORDER BY Id
"""

_SQL_CONTEO_POR_ESTADO = """
SELECT
    EI.Id AS id_estado,
    EI.Descripcion AS estado,
    COUNT(*) AS cantidad
FROM dbo.Incidente I
INNER JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
WHERE I.ID_Tipo_Incidente IN (101, 108)
  AND I.Fecha_Ingreso >= DATEADD(MONTH, -24, GETDATE())
GROUP BY EI.Id, EI.Descripcion
ORDER BY cantidad DESC
"""

_SQL_CONTEO_POR_ESTADO_TODOS_TIPOS = """
SELECT
    TI.Descripcion AS tipo,
    EI.Descripcion AS estado,
    COUNT(*) AS cantidad
FROM dbo.Incidente I
INNER JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
INNER JOIN dbo.Tipo_Incidente TI ON I.ID_Tipo_Incidente = TI.Id
WHERE I.Fecha_Ingreso >= DATEADD(MONTH, -6, GETDATE())
GROUP BY TI.Descripcion, EI.Descripcion
ORDER BY cantidad DESC
"""

_SQL_COLUMNAS_INCIDENTE = """
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Incidente'
ORDER BY ORDINAL_POSITION
"""

_SQL_CORRELATIVIDAD = """
SELECT TOP 50 * FROM dbo.Estado_Incidente_ST_Correlatividad ORDER BY ID_Estado_Desde
"""

_SQL_MOTIVO_FINALIZACION = """
SELECT * FROM dbo.MotivoFinalizacion ORDER BY Id
"""

_SQL_VW_INFORME_MUESTRA = """
SELECT TOP 5 * FROM dbo.VW_InformeIncidenteST
"""

_SQL_VW_COLUMNAS = """
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'VW_InformeIncidenteST'
ORDER BY ORDINAL_POSITION
"""

# Muestra de incidentes de tipos (101,108) con fecha_ingreso reciente para ver
# qué estado tienen los que parecerían "pendientes a cerrar"
_SQL_MUESTRA_INCIDENTES_RECIENTES = """
SELECT TOP 20
    I.ID_Incidente,
    I.Fecha_Ingreso,
    TI.Descripcion AS tipo,
    EI.Descripcion AS estado,
    EI.Id AS id_estado,
    E1.Den_Comercial AS tecnico
FROM dbo.Incidente I
INNER JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
INNER JOIN dbo.Tipo_Incidente TI ON I.ID_Tipo_Incidente = TI.Id
INNER JOIN dbo.Empresa E1 ON I.ID_Tecnico = E1.ID_Empresa
WHERE I.ID_Tipo_Incidente IN (101, 108)
  AND I.Fecha_Ingreso >= DATEADD(MONTH, -3, GETDATE())
ORDER BY I.Fecha_Ingreso DESC
"""

# Ver si incidentes con estado "finalizado" (si existe) tienen o no fila en IncidenteTiempo
_SQL_SIN_TIEMPO = """
SELECT
    EI.Id AS id_estado,
    EI.Descripcion AS estado,
    COUNT(*) AS total,
    SUM(CASE WHEN IT.ID_Incidente IS NULL THEN 1 ELSE 0 END) AS sin_tiempo
FROM dbo.Incidente I
INNER JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
LEFT JOIN dbo.IncidenteTiempo IT ON IT.ID_Incidente = I.ID_Incidente
WHERE I.ID_Tipo_Incidente IN (101, 108)
  AND I.Fecha_Ingreso >= DATEADD(MONTH, -24, GETDATE())
GROUP BY EI.Id, EI.Descripcion
ORDER BY total DESC
"""


def _catalogo_estado(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_CATALOGO_ESTADO)
    filas = list(cursor.fetchall())
    print(f"\n=== Catálogo Estado_Incidente ({len(filas)}) ===")
    for f in filas:
        print(f"  Id={f.Id}  {f.Descripcion!r}")


def _conteo_por_estado_tipos_st(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_CONTEO_POR_ESTADO)
    filas = list(cursor.fetchall())
    print(f"\n=== Incidentes tipo (101,108) por estado — últimos 24 meses ({len(filas)} estados) ===")
    for f in filas:
        print(f"  id={f.id_estado}  {f.estado!r}: {f.cantidad}")


def _conteo_por_tipo_y_estado(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_CONTEO_POR_ESTADO_TODOS_TIPOS)
    filas = list(cursor.fetchall())
    print(f"\n=== Incidentes todos los tipos por estado — últimos 6 meses (top {len(filas)}) ===")
    for f in filas:
        print(f"  {f.tipo!r} / {f.estado!r}: {f.cantidad}")


def _columnas_incidente(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_COLUMNAS_INCIDENTE)
    filas = list(cursor.fetchall())
    print(f"\n=== Columnas de dbo.Incidente ({len(filas)}) ===")
    for f in filas:
        print(f"  {f.COLUMN_NAME}  ({f.DATA_TYPE}, nullable={f.IS_NULLABLE})")


def _correlatividad(cursor: pyodbc.Cursor) -> None:
    try:
        cursor.execute(_SQL_CORRELATIVIDAD)
        filas = list(cursor.fetchall())
        cols = [d[0] for d in cursor.description]
        print(f"\n=== Estado_Incidente_ST_Correlatividad ({len(filas)} filas) ===")
        print("  Columnas:", cols)
        for f in filas:
            print(" ", dict(zip(cols, f)))
    except pyodbc.Error as e:
        print(f"\n=== Estado_Incidente_ST_Correlatividad — NO EXISTE o error: {e} ===")


def _motivo_finalizacion(cursor: pyodbc.Cursor) -> None:
    try:
        cursor.execute(_SQL_MOTIVO_FINALIZACION)
        filas = list(cursor.fetchall())
        cols = [d[0] for d in cursor.description]
        print(f"\n=== MotivoFinalizacion ({len(filas)} filas) ===")
        print("  Columnas:", cols)
        for f in filas:
            print(" ", dict(zip(cols, f)))
    except pyodbc.Error as e:
        print(f"\n=== MotivoFinalizacion — NO EXISTE o error: {e} ===")


def _vista_informe_columnas(cursor: pyodbc.Cursor) -> None:
    try:
        cursor.execute(_SQL_VW_COLUMNAS)
        filas = list(cursor.fetchall())
        print(f"\n=== VW_InformeIncidenteST — columnas ({len(filas)}) ===")
        for f in filas:
            print(f"  {f.COLUMN_NAME}  ({f.DATA_TYPE})")
    except pyodbc.Error as e:
        print(f"\n=== VW_InformeIncidenteST — NO EXISTE o error: {e} ===")


def _vista_informe_muestra(cursor: pyodbc.Cursor) -> None:
    try:
        cursor.execute(_SQL_VW_INFORME_MUESTRA)
        filas = list(cursor.fetchall())
        if not filas:
            print("\n=== VW_InformeIncidenteST — sin filas ===")
            return
        cols = [d[0] for d in cursor.description]
        print(f"\n=== VW_InformeIncidenteST — muestra de {len(filas)} filas ===")
        print("  Columnas:", cols)
        for f in filas:
            print(" ", dict(zip(cols, f)))
    except pyodbc.Error as e:
        print(f"\n=== VW_InformeIncidenteST — error al consultar: {e} ===")


def _incidentes_con_y_sin_tiempo(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_SIN_TIEMPO)
    filas = list(cursor.fetchall())
    print(f"\n=== Incidentes (101,108) últimos 24m: con/sin fila en IncidenteTiempo ===")
    for f in filas:
        print(f"  id={f.id_estado} {f.estado!r}: total={f.total} sin_tiempo={f.sin_tiempo}")


def _muestra_recientes(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_MUESTRA_INCIDENTES_RECIENTES)
    filas = list(cursor.fetchall())
    print(f"\n=== Muestra incidentes recientes (101,108) — últimos 3 meses ({len(filas)} filas) ===")
    for f in filas:
        print(
            f"  ID={f.ID_Incidente}  Ingreso={f.Fecha_Ingreso}  "
            f"Tipo={f.tipo!r}  Estado={f.estado!r}(id={f.id_estado})  "
            f"Tecnico={f.tecnico!r}"
        )


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit("Falta SLA_MERCURIO_HOST en .env — no hay acceso a MERCURIO desde este entorno.")

    conn_str = build_mercurio_connection_string(settings)
    print("Conectando a MERCURIO…")
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _catalogo_estado(cursor)
        _conteo_por_estado_tipos_st(cursor)
        _conteo_por_tipo_y_estado(cursor)
        _incidentes_con_y_sin_tiempo(cursor)
        _muestra_recientes(cursor)
        _columnas_incidente(cursor)
        _correlatividad(cursor)
        _motivo_finalizacion(cursor)
        _vista_informe_columnas(cursor)
        _vista_informe_muestra(cursor)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
